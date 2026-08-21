# CarKitInstrument

A **diagnostic, observe-only** rootless tweak for a Dopamine-jailbroken
iPhone (tested target: iPhone 8 Plus, iOS 16.6). It hooks a small set of
CarKit / CarPlay / FrontBoard classes and **logs** their state during one
genuine Carlinkit CarPlay connection.

It is the "purpose-built instrumentation tweak" step: before we can attempt
a software-only CarPlay session, we need to see what the real objects
actually contain and — crucially — **who creates each of them**.

## What it does (and does not do)

* **Does:** log `CARSession`, `CARSessionConfiguration`, `CARScreenInfo`,
  `CARScreenViewArea`, `FBSDisplaySource`, `FBSDisplayConfiguration`,
  `FBSDisplayMode` — their properties, `description`, allocation backtraces,
  and the `CRCarPlayCapabilitiesManager` callbacks that hand us the live
  session. Also logs the `CARSessionScreenBecameAvailableNotification`.
* **Does not:** change any behaviour, patch MFi authentication, read or copy
  any authentication key, or fake a screen. Every hook calls the original
  implementation and only records. This is a measurement instrument, not the
  final tweak.

## Why this design

* **`+alloc` hooks** fire no matter which `initWith…:` an object is built
  with, so the backtrace captured there answers the open question from the
  logs: *does `CARSession` create the `FBSDisplaySource`, or does an AirPlay/
  display service create it and `CARSession` merely discover it?* Compare the
  `+[CARSession alloc]` and `+[FBSDisplaySource alloc]` backtraces and their
  ordering to read the dependency direction.
* **`CRCarPlayCapabilitiesManager` hooks** give us the fully-connected,
  configured session object to dump (the alloc site catches it empty).
* The dumper walks one level into nested `CAR*/CR*/FBS*/UIScreen*/_UI*`
  values, so a single `sessionDidConnect:` dump yields
  session → configuration → screenInfo → screen in one place.

## Privacy

Wi-Fi PSK / pairing-key-style values are **redacted by default** (they are
not needed for display-session replay). SSIDs, accessory names, and screen
geometry are kept because they are useful context — so still treat the log
as private and don't paste the raw file into a public issue. Edit the
`bad` list in `Tweak.x` (`CKKeyIsSecret`) to redact more.

## Build

Requires [Theos](https://theos.dev) with the **rootless** SDK on your build
machine (Mac, or Linux with the iOS toolchain).

```sh
cd carkit-instrument
make package FINALPACKAGE=1
```

The `.deb` lands in `./packages/`. `ARCHS = arm64 arm64e` covers the A11
(iPhone 8 Plus) — the `arm64e` slice is what lets it inject into system
daemons like `carkitd`.

## Install

1. Copy the `.deb` to the phone (AirDrop, `scp`, or Sileo's "install local
   package").
2. In **Sileo**: install it, then let it restart `SpringBoard`/`carkitd`
   (the Makefile's `after-install` does this).
3. Verify it loaded — in a terminal on-device:
   ```sh
   ls -la /var/mobile/Documents/CarKitInstrument/
   ```
   You should see `instr-carkitd-<pid>.log`, `instr-SpringBoard-<pid>.log`,
   and (once CarPlay UI comes up) `instr-CarPlay-<pid>.log`. Everything is
   also mirrored to `os_log` (subsystem `com.cf.carkitinstrument`), viewable
   in Console.app or with `oslog`/`idevicesyslog`.

## Capture procedure

1. Fresh boot is cleanest. Confirm the log dir is empty (or note the current
   sizes).
2. Connect the **Carlinkit** and let CarPlay come up fully on the head unit
   (or your Tesla-Android + Carlinkit rig) exactly as you do today.
3. Leave it connected ~30–60 s, interact once (so a mode/scene change fires),
   then disconnect.
4. Collect the logs:
   ```sh
   tar czf ~/carkit-capture.tgz -C /var/mobile/Documents CarKitInstrument
   ```
5. The interesting anchors to grep for first:
   * `sessionDidConnect:` — the live session dump
   * `+[CARSession alloc]` / `+[FBSDisplaySource alloc]` — creation + caller
   * `CARSessionScreenBecameAvailableNotification` — screen goes live
   * `CARScreenInfo` — confirm `960x736 @ 30`, interaction models, `isLimited`

## What to look at next (maps to the plan)

The one question that decides how hard the final tweak is:

> Is the `FBSDisplaySource` created **by** the `CARSession`, or by a separate
> AirPlay/display service that the `CARSession` then attaches to?

Read it straight off the backtraces:
* If `+[FBSDisplaySource alloc]`'s backtrace runs through CarKit/CARSession
  frames → the session drives the display, and a synthetic local session is
  plausible.
* If it runs through an AirPlay receiver / display-service framework →
  the display is created upstream and `CARSession` only discovers it, so the
  synthetic path has to stand up that service too.

Once that's known, the follow-up experiment (synthetic `CARScreenInfo`
960×736@30 → FrontBoard display source → CarPlay `UIWindowScene`, then
capture the local framebuffer/IOSurface → H.264 → WebSocket → Tesla browser)
can be scoped for real instead of guessed at.

## Files

| File | Purpose |
|------|---------|
| `Tweak.x` | The hooks + dumper + logger |
| `Makefile` | Rootless Theos build config |
| `control` | Debian package metadata for Sileo |
| `CarKitInstrument.plist` | Inject filter: `carkitd`, SpringBoard, CarPlay |
