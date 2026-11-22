# Basilisk on Haiku: build status (config agent)

Branch: `haiku-config` (Basilisk) and `haiku-config` (platform/UXP).
mozconfig: `mozconfig-haiku` (cairo-haiku, system nspr/nss/zlib/bz2/jpeg/ffi,
no jemalloc/crashreporter/updater/webrtc/npapi/dbus/pulseaudio/gamepad).
Run mach with `python3.12 ./mach ...` (the VM's `python3` is 3.14).

## Build-system support in haiku-config

- moz.configure: `*-haiku` triple -> kernel/os `Haiku`, `XP_HAIKU` (+ `XP_UNIX`),
  `__HAIKU__` kernel check, gyp OS `haiku`.
- Toolkit `cairo-haiku` (default on Haiku): `MOZ_WIDGET_TOOLKIT=haiku`,
  `MOZ_WIDGET_HAIKU`, no `MOZ_X11`/`MOZ_WIDGET_GTK`/GLX. `TK_LIBS` =
  `-lbe -ltranslation -lmedia -lnetwork -lbsd`, linked into libxul.
  `widget/moz.build` + `widget/haiku/` belong to the widget agent.
- old-configure (top and js/src): Haiku case adds `-lnetwork -lbsd` to LDFLAGS;
  pthreads come from libroot (no -lpthread); no PulseAudio default.
- `--with-system-nspr` (pkg-config `nspr`) and `--with-system-nss` (pkg-config `nss`).
  With system NSS, `security/` is skipped; `config/external/nss` provides the
  `nss` library and builds `mozpkix` from the in-tree sources; crmf is dropped (unused).

## VM status (haiku-config + haiku-widget diff, /boot/home/work/config)

- `MOZCONFIG=.../mozconfig-haiku python3.12 platform/mach configure` (run from the
  Basilisk root) **passes**: 892 moz.build files, RecursiveMake backend written.
  config.status: OS_ARCH=Haiku, MOZ_WIDGET_TOOLKIT=haiku, MOZ_WIDGET_HAIKU, XP_HAIKU,
  MOZ_SYSTEM_NSS=1, MOZ_USER_DIR="Mozilla", no MOZ_X11.
  Needs widget/haiku (haiku-widget), since stock widget/moz.build adds
  LOCAL_INCLUDES '/widget/<toolkit>'. The real full build is `haiku-all` (integrator).
- `mach build`: export (IDL, WebIDL, IPDL, headers) completes and C/C++ compilation
  runs. Third-party C/C++ (ICU, sqlite, harfbuzz, skia, pixman/cairo, libvpx,
  libtheora, libyuv, libjxl, ...) compile without errors.
- VM notes: no `patch` (use `git apply --directory=platform`), no `nasm`
  (so --disable-av1), and `python3` is 3.14 (use python3.12).

## First C++ errors by area (haiku-config alone, make -k)

- ipc (owned by haiku-ipc; fixed there):
  `ipc/chromium/src/build/build_config.h:39:2: error: #error Please add support for your platform in build/build_config.h`
  This breaks almost everything that includes ipc/chromium headers (dom/base, dom/canvas,
  dom/events, dom/heapsnapshot, ...). Base also passes -DOS_LINUX=1 via chromium-config.
- xpcom/mozglue (owned by haiku-xpcom; fixed there):
  `mozglue/misc/TimeStamp_posix.cpp:15: dist/system_wrappers/sys/syscall.h:3:15: fatal error: sys/syscall.h: No such file or directory`
- build system (fixed in haiku-config): with system NSPR, recurse.mk ordered
  config/external/nss after the nonexistent nspr/pr, ds and libc targets.
