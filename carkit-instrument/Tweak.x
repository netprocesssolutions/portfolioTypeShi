// CarKitInstrument — observe-only diagnostic tweak
// ------------------------------------------------
// Goal: during ONE genuine Carlinkit CarPlay connection, record the real
// CarKit / CarPlay / FrontBoard object graph so we can see:
//   * what the connected CARSession / CARSessionConfiguration actually contain
//   * the CARScreenInfo (pixelSize, fps, interaction models, isLimited, ...)
//   * the FBSDisplaySource / FBSDisplayConfiguration / FBSDisplayMode state
//   * and CRITICALLY who allocates/creates each of these (via backtrace)
//
// It hooks nothing destructively: every hook calls %orig and only logs.
// It does not touch MFi authentication and does not read/copy any key.
//
// Injected into: carkitd, SpringBoard, CarPlay (see CarKitInstrument.plist).
// Classes absent from a given process simply don't get hooked (safe no-op).

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <objc/runtime.h>
#import <os/log.h>
#import <unistd.h>

// ===================== logging core =====================

static os_log_t CKLog(void) {
    static os_log_t l;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ l = os_log_create("com.cf.carkitinstrument", "instr"); });
    return l;
}

static NSFileHandle *gLogFH = nil;
static NSString     *gLogPath = nil;
static dispatch_queue_t gLogQ = NULL;

static void CKOpenLog(void) {
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        gLogQ = dispatch_queue_create("com.cf.carkitinstrument.log", DISPATCH_QUEUE_SERIAL);
        NSString *proc = [NSProcessInfo processInfo].processName ?: @"unknown";
        pid_t pid = getpid();
        // Try a few sinks; daemons and SpringBoard run as different users, so
        // fall back until one is writable. Per-process file avoids clobbering.
        NSArray<NSString *> *dirs = @[ @"/var/mobile/Documents/CarKitInstrument",
                                       @"/var/tmp/CarKitInstrument",
                                       NSTemporaryDirectory() ];
        NSFileManager *fm = [NSFileManager defaultManager];
        for (NSString *d in dirs) {
            if (!d.length) continue;
            [fm createDirectoryAtPath:d withIntermediateDirectories:YES
                           attributes:@{ NSFilePosixPermissions : @(0777) } error:NULL];
            NSString *p = [d stringByAppendingPathComponent:
                           [NSString stringWithFormat:@"instr-%@-%d.log", proc, pid]];
            if (![fm fileExistsAtPath:p])
                [fm createFileAtPath:p contents:[NSData data] attributes:nil];
            NSFileHandle *fh = [NSFileHandle fileHandleForWritingAtPath:p];
            if (fh) { [fh seekToEndOfFile]; gLogFH = fh; gLogPath = p; break; }
        }
        os_log(CKLog(), "CarKitInstrument loaded in %{public}@ (pid %d); file=%{public}@",
               proc, pid, gLogPath ?: @"(os_log only)");
    });
}

static NSString *CKTimestamp(void) {
    // Only ever called on gLogQ (NSDateFormatter is not thread-safe).
    static NSDateFormatter *df;
    static dispatch_once_t o;
    dispatch_once(&o, ^{
        df = [NSDateFormatter new];
        df.dateFormat = @"yyyy-MM-dd HH:mm:ss.SSS";
        df.locale = [NSLocale localeWithLocaleIdentifier:@"en_US_POSIX"];
    });
    return [df stringFromDate:[NSDate date]];
}

static void CKLine(NSString *msg) {
    if (!msg) return;
    CKOpenLog();
    os_log(CKLog(), "%{public}s", msg.UTF8String ?: "");
    if (!gLogQ) return;
    dispatch_async(gLogQ, ^{
        NSString *line = [NSString stringWithFormat:@"%@ [%@:%d] %@\n",
                          CKTimestamp(),
                          [NSProcessInfo processInfo].processName ?: @"?",
                          getpid(), msg];
        @try { [gLogFH writeData:[line dataUsingEncoding:NSUTF8StringEncoding]]; }
        @catch (__unused NSException *e) {}
    });
}

// ===================== introspection helpers =====================

static BOOL CKKeyIsSecret(NSString *key) {
    NSString *k = key.lowercaseString;
    static NSArray<NSString *> *bad;
    static dispatch_once_t o;
    dispatch_once(&o, ^{
        // Wi-Fi PSK / pairing material is never needed for display-session
        // replay, so redact it by default. Everything else is kept.
        bad = @[ @"password", @"passphrase", @"psk", @"pmk", @"credential",
                 @"secret", @"privatekey", @"wifikey", @"pairingkey",
                 @"sharedkey", @"presharedkey" ];
    });
    for (NSString *b in bad) if ([k containsString:b]) return YES;
    return NO;
}

static NSString *CKDescribe(id v) {
    if (!v) return @"(nil)";
    @try {
        if ([v isKindOfClass:[NSData class]])
            return [NSString stringWithFormat:@"<NSData len=%lu>", (unsigned long)[(NSData *)v length]];
        NSString *s = [v description];
        if (s.length > 800) s = [[s substringToIndex:800] stringByAppendingString:@"…(trunc)"];
        return s ?: @"(nil-desc)";
    } @catch (__unused NSException *e) { return @"(description threw)"; }
}

static NSString *CKBacktrace(void) {
    @try {
        NSArray<NSString *> *sym = [NSThread callStackSymbols];
        NSUInteger n = MIN((NSUInteger)20, sym.count);
        NSArray *top = [sym subarrayWithRange:NSMakeRange(0, n)];
        return [top componentsJoinedByString:@"\n    "];
    } @catch (__unused NSException *e) { return @"(backtrace unavailable)"; }
}

// Recursively dump an object's declared properties (up to but not including
// NSObject) plus [description]. Recurses one extra level into CAR*/CR*/FBS*/
// UIScreen*/_UI* values so we get session -> config -> screenInfo -> screen.
static void CKDumpInto(NSMutableString *out, id obj, int depth, NSMutableSet *seen) {
    if (out.length > 300000) return;                 // runaway guard
    NSString *pad = [@"" stringByPaddingToLength:(NSUInteger)(depth * 2)
                                      withString:@" " startingAtIndex:0];
    if (!obj)                       { [out appendFormat:@"%@(nil)\n", pad]; return; }
    if (obj == (id)[NSNull null])   { [out appendFormat:@"%@(nil arg)\n", pad]; return; }

    Class cls = object_getClass(obj);
    NSString *addr = [NSString stringWithFormat:@"%p", (void *)obj];
    if ([seen containsObject:addr]) {
        [out appendFormat:@"%@<%@ %@> (already dumped)\n", pad, NSStringFromClass(cls), addr];
        return;
    }
    [seen addObject:addr];

    [out appendFormat:@"%@<%@ %@>\n", pad, NSStringFromClass(cls), addr];
    [out appendFormat:@"%@  description: %@\n", pad, CKDescribe(obj)];

    Class c = cls;
    while (c && c != [NSObject class]) {
        unsigned int n = 0;
        objc_property_t *props = class_copyPropertyList(c, &n);
        for (unsigned int i = 0; i < n; i++) {
            const char *pn = property_getName(props[i]);
            if (!pn) continue;
            NSString *key = [NSString stringWithUTF8String:pn];
            id val = nil;
            @try { val = [obj valueForKey:key]; }
            @catch (__unused NSException *e) { val = @"(KVC threw)"; }

            if (CKKeyIsSecret(key)) {
                unsigned long len = 0;
                @try { if ([val respondsToSelector:@selector(length)]) len = (unsigned long)[val length]; }
                @catch (__unused NSException *e) {}
                [out appendFormat:@"%@  .%@ = <redacted len=%lu>\n", pad, key, len];
                continue;
            }

            [out appendFormat:@"%@  .%@ = %@\n", pad, key, CKDescribe(val)];

            if (val && val != (id)[NSNull null] && depth < 3) {
                Class vc = object_getClass(val);
                NSString *vcn = NSStringFromClass(vc);
                if ([vcn hasPrefix:@"CAR"] || [vcn hasPrefix:@"CR"] ||
                    [vcn hasPrefix:@"FBS"] || [vcn hasPrefix:@"FB"] ||
                    [vcn hasPrefix:@"UIScreen"] || [vcn hasPrefix:@"_UI"]) {
                    CKDumpInto(out, val, depth + 1, seen);
                }
            }
        }
        if (props) free(props);
        c = class_getSuperclass(c);
    }
}

// Log a hook event: self, each argument, a full dump, and a backtrace.
static void CKEvent(NSString *tag, id slf, SEL cmd, NSArray *args) {
    NSMutableString *s = [NSMutableString string];
    [s appendFormat:@"\n===== %@ =====\n", tag];
    [s appendFormat:@"selector: %@\n", NSStringFromSelector(cmd)];
    NSMutableSet *seen = [NSMutableSet set];
    [s appendString:@"self:\n"];
    CKDumpInto(s, slf, 0, seen);
    int i = 0;
    for (id a in args) {
        [s appendFormat:@"arg[%d]:\n", i++];
        CKDumpInto(s, a, 0, seen);
    }
    [s appendFormat:@"backtrace:\n    %@\n", CKBacktrace()];
    CKLine(s);
}

// Log allocation of a data class + who allocated it.
static void CKAlloc(NSString *clsName, id obj) {
    CKLine([NSString stringWithFormat:@"\n+++++ +[%@ alloc] -> %p +++++\nbacktrace:\n    %@",
            clsName, (void *)obj, CKBacktrace()]);
}

// ===================== hooks: CarKit capabilities manager =====================
// These deliver the live, connected session object to us.

%hook CRCarPlayCapabilitiesManager
- (void)sessionDidConnect:(id)session {
    CKEvent(@"CRCarPlayCapabilitiesManager sessionDidConnect:", self, _cmd,
            @[ session ?: [NSNull null] ]);
    %orig;
}
- (void)sessionDidDisconnect:(id)session {
    CKEvent(@"CRCarPlayCapabilitiesManager sessionDidDisconnect:", self, _cmd,
            @[ session ?: [NSNull null] ]);
    %orig;
}
- (void)_worker_queue_setSession:(id)session {
    CKEvent(@"CRCarPlayCapabilitiesManager _worker_queue_setSession:", self, _cmd,
            @[ session ?: [NSNull null] ]);
    %orig;
}
- (void)accessoryManager:(id)mgr didConnectVehicleAccessory:(id)acc {
    CKEvent(@"CRCarPlayCapabilitiesManager accessoryManager:didConnectVehicleAccessory:",
            self, _cmd, @[ mgr ?: [NSNull null], acc ?: [NSNull null] ]);
    %orig;
}
// "resolve X for Y" — assumed to return the resolved capabilities object.
// We log entry (with the session) and pass the real return through untouched.
- (id)resolveCapabilitiesForSession:(id)session {
    CKEvent(@"CRCarPlayCapabilitiesManager resolveCapabilitiesForSession:", self, _cmd,
            @[ session ?: [NSNull null] ]);
    return %orig;
}
%end

// ===================== hooks: session configuration =====================

%hook CARSessionConfiguration
- (void)updateCarCapabilities {
    CKEvent(@"CARSessionConfiguration updateCarCapabilities (before)", self, _cmd, @[]);
    %orig;
    CKEvent(@"CARSessionConfiguration updateCarCapabilities (after)", self, _cmd, @[]);
}
// Some builds take an argument; if this selector doesn't exist the hook no-ops.
- (void)updateCarCapabilities:(id)caps {
    CKEvent(@"CARSessionConfiguration updateCarCapabilities: (before)", self, _cmd,
            @[ caps ?: [NSNull null] ]);
    %orig;
    CKEvent(@"CARSessionConfiguration updateCarCapabilities: (after)", self, _cmd,
            @[ caps ?: [NSNull null] ]);
}
%end

// ===================== hooks: allocation sites =====================
// +alloc fires regardless of which initWith... is used, so the backtrace here
// tells us exactly who creates each object.

%hook CARSession
+ (id)alloc { id o = %orig; CKAlloc(@"CARSession", o); return o; }
%end

%hook CARSessionConfiguration
+ (id)alloc { id o = %orig; CKAlloc(@"CARSessionConfiguration", o); return o; }
%end

%hook CARScreenInfo
+ (id)alloc { id o = %orig; CKAlloc(@"CARScreenInfo", o); return o; }
%end

%hook CARScreenViewArea
+ (id)alloc { id o = %orig; CKAlloc(@"CARScreenViewArea", o); return o; }
%end

%hook FBSDisplaySource
+ (id)alloc { id o = %orig; CKAlloc(@"FBSDisplaySource", o); return o; }
%end

%hook FBSDisplayConfiguration
+ (id)alloc { id o = %orig; CKAlloc(@"FBSDisplayConfiguration", o); return o; }
%end

%hook FBSDisplayMode
+ (id)alloc { id o = %orig; CKAlloc(@"FBSDisplayMode", o); return o; }
%end

// ===================== constructor: notifications =====================

%ctor {
    @autoreleasepool {
        CKOpenLog();

        // The precise "screen is now live" signal.
        [[NSNotificationCenter defaultCenter]
            addObserverForName:@"CARSessionScreenBecameAvailableNotification"
                        object:nil queue:nil
                    usingBlock:^(NSNotification *note) {
            NSMutableString *s = [NSMutableString stringWithString:
                @"\n##### CARSessionScreenBecameAvailableNotification #####\n"];
            NSMutableSet *seen = [NSMutableSet set];
            [s appendString:@"object:\n"];
            CKDumpInto(s, note.object, 0, seen);
            [s appendFormat:@"userInfo: %@\n", note.userInfo];
            [s appendFormat:@"backtrace:\n    %@\n", CKBacktrace()];
            CKLine(s);
        }];

        // Cheap discovery of any other CarPlay/CAR* notifications we didn't
        // know to look for. Logs name + object class only (kept light).
        [[NSNotificationCenter defaultCenter]
            addObserverForName:nil object:nil queue:nil
                    usingBlock:^(NSNotification *note) {
            NSString *n = note.name;
            if (!n) return;
            if ([n hasPrefix:@"CARSession"] || [n hasPrefix:@"CAR"] ||
                [n hasPrefix:@"CarPlay"] || [n containsString:@"CarPlay"]) {
                CKLine([NSString stringWithFormat:@"[notif] %@ object=%@",
                        n, object_getClass(note.object)]);
            }
        }];

        CKLine(@"CarKitInstrument %ctor complete — observers registered.");
    }
}
