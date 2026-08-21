# CarKitInstrument — rootless Theos tweak (Dopamine / ElleKit)
#
# Diagnostic-only. Hooks a handful of CarKit / CarPlay / FrontBoard classes
# and *logs* their state during a genuine CarPlay connection. It does not
# modify behaviour, patch authentication, or copy any MFi material.
#
# Build (on a Mac/Linux with Theos + the rootless SDK):
#   make package FINALPACKAGE=1
# Then AirDrop / scp the .deb from ./packages/ and install via Sileo.

export ARCHS = arm64 arm64e
export TARGET = iphone:clang:16.5:15.0
export THEOS_PACKAGE_SCHEME = rootless

# Restart these after install so the tweak loads immediately.
INSTALL_TARGET_PROCESSES = carkitd SpringBoard CarPlay

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = CarKitInstrument

CarKitInstrument_FILES   = Tweak.x
CarKitInstrument_CFLAGS  = -fobjc-arc
CarKitInstrument_FRAMEWORKS = Foundation UIKit

include $(THEOS_MAKE_PATH)/tweak.mk

after-install::
	install.exec "killall -9 carkitd SpringBoard 2>/dev/null || true"
