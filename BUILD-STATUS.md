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

## VM status

- configure: OK
- export: running
- compile: mfbt, mozglue, memory, xpcom compile (verified per directory before integration)
- libxul link: not reached yet
- basilisk binary: not reached yet

## Current blocking errors

(none yet)
