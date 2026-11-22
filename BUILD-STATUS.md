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

## Integration (branch `haiku-all`, Basilisk and platform)

`haiku-all` merges haiku-config, haiku-js, haiku-xpcom, haiku-ipc,
haiku-widget and haiku-misc (one trivial conflict in
mozglue/misc/TimeStamp_posix.cpp). Full build runs in the VM at
/boot/home/work/xpcom (src, obj), `./mach build` with MOZ_MAKE_FLAGS=-j10
(note: top-level `mach` is a sh script; run `./mach`, not `python3.12 ./mach`).

## VM status (haiku-all, /boot/home/work/xpcom)

- configure: OK
- export: OK (`make install-manifests` + export tier)
- compile: run 1 got ~18 min into the compile tier; only error was
  printingui/unixshared missing nsIPrintDialogService.h (fixed on haiku-all).
  Run 2 (`-k`, collect all errors) in progress.
- libxul link: not reached yet
- basilisk binary: not reached yet

## Fixed on haiku-all during integration

- config/recurse.mk: nss -> in-tree nspr dependency only with MOZ_BUILD_NSPR
- toolkit/library: link FT2_LIBS for the haiku toolkit
- widget/moz.build: export nsIPrintDialogService.h for haiku

## Current blocking errors

(none known; run 2 in progress)

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
