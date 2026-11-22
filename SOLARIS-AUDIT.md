# Audit of the files UXP's Solaris port touched (todo-solaris-files.txt)

For each of the 76 files: whether Haiku needs a case, and what was done.
"Fixed" means a change on platform `haiku-config` (commit "Haiku: Solaris-audit fixes"),
compile-checked in the VM where noted.

Background that decides many entries: Haiku's gcc defines `__HAIKU__` and `__ELF__`,
but **not** `__unix__`/`unix`. Its readelf/nm/objdump are GNU binutils, its ld is GNU ld,
`/bin/sh` is bash, `madvise`/`posix_madvise`, `alloca` (via stdlib.h), `setenv` and
`nl_langinfo(CODESET)` all exist. NPAPI, jemalloc, updater, crash reporter, WebRTC and
necko-wifi are off in mozconfig-haiku; NSPR, NSS and libffi come from the system.

## Fixed on haiku-config

| File | Change |
|---|---|
| gfx/angle/src/common/platform.h | `__HAIKU__` is `ANGLE_PLATFORM_POSIX` (was `#error Unsupported platform`). VM: gfx/angle compiles. |
| (related) gfx/angle/include/EGL/eglplatform.h | Haiku branch before `__unix__` (generic types, as upstream Khronos). Was `#error "Platform not recognized"`. VM: gfx/angle compiles (10 objects). |
| gfx/ycbcr/moz.build | Haiku uses `yuv_row_posix.cpp` like Linux/BSD/Solaris. VM: yuv_row_posix.o builds. |
| security/generate_mapfile.py | Accept Haiku (ELF + GNU ld), only matters for in-tree NSS. |
| build/unix/run-mozilla.sh | Also set `LIBRARY_PATH`, which Haiku's runtime loader uses instead of `LD_LIBRARY_PATH`. |
| build/moz.configure/memory.configure | Not edited: `--enable-jemalloc` dies on Haiku with a clear message, which is right while jemalloc is unported (system malloc). |

## Nothing needed (one-line reason each)

| File | Reason |
|---|---|
| build/autoconf/acspecific.m4 | Only comments mention SunOS. |
| config/config.mk | `ELF_TEST` uses readelf, which Haiku has (elfdump is the Solaris oddity). |
| config/rules.mk | Haiku uses GNU ld, so the `GCC_USE_GNU_LD` version-script path applies. |
| config/external/ffi/moz.build | System libffi (`--with-system-ffi`); in-tree libffi defaults would also suit x86_64 ELF. |
| config/external/icu/data/icudata_gas.S | GNU as/ELF: `.section .rodata` is right; Solaris case is an exception. |
| config/external/nspr/pr/moz.build | System NSPR (`--with-system-nspr`); in-tree nsprpub has no Haiku port. |
| db/sqlite3/src/sqlite3.c | Unknown OS gets `SQLITE_MAX_MMAP_SIZE 0` (mmap I/O off): safe default, vendored file. |
| dom/base/nsContentUtils.h | `<ieeefp.h>` is Solaris-only. |
| dom/media/AudioStream.h | Solaris-only SoundTouch header workaround. |
| dom/plugins/base/npapi.h | Generic XP_UNIX + GCC path applies. |
| dom/plugins/base/nptypes.h | Haiku has `<stdint.h>`; default branch applies. |
| dom/plugins/base/nsPluginsDirUnix.cpp | NPAPI disabled; Solaris bits are plugin-path specifics. |
| dom/plugins/ipc/PluginMessageUtils.cpp | NPAPI off; Linux/Solaris X11 plugin paths. |
| dom/plugins/ipc/PluginModuleChild.cpp | NPAPI off; GTK/X11 plugin code. |
| dom/plugins/ipc/PluginModuleChild.h | Same. |
| editor/reftests/xul/platform.js | Tests are disabled; UA sniffing for reftest only. |
| extensions/spellcheck/hunspell/src/moz.build | Solaris-only linking workaround (UXP #2290); shared hunspell is fine on Haiku. |
| gfx/cairo/cairo/src/cairo-compiler-private.h | Solaris excluded from ELF visibility; Haiku is ELF and wants it. |
| gfx/cairo/libpixman/src/pixman-compiler.h | Sun Studio compiler cases only. |
| gfx/cairo/libpixman/src/pixman.h | Falls to `<stdint.h>`. Compiled in the VM. |
| gfx/harfbuzz/src/hb-common.h | Falls to `<stdint.h>`. Compiled in the VM. |
| gfx/qcms/qcmstypes.h | Falls to `<stdint.h>`. |
| gfx/skia/patches/archive/0009-Bug-755869-FreeBSD-Hurd.patch | Archived patch, not built. (SkPreConfig.h is handled on haiku-widget.) |
| intl/locale/unix/unixcharset.properties | Deprecated table; Haiku has `nl_langinfo(CODESET)`. |
| ipc/chromium/src/base/message_pump_glib.cc | GLib pump isn't used without GTK. Owned by ipc. |
| ipc/chromium/src/base/message_pump_libevent.cc | Solaris-only `<sys/stat.h>` include. Owned by ipc. |
| ipc/chromium/src/base/time.h | Solaris-only timespec helpers. Owned by ipc. |
| ipc/chromium/src/third_party/libevent/arc4random.c | Solaris-only include. libevent config is done on haiku-ipc. |
| ipc/chromium/src/third_party/libevent/buffer.c | Solaris sendfile variant; generic path otherwise. |
| ipc/chromium/src/third_party/libevent/event.c | Solaris-only RNG-lock workaround. |
| ipc/chromium/src/third_party/libevent/m4/acx_pthread.m4 | Autoconf m4, not used by the moz.build. |
| ipc/glue/BrowserProcessSubThread.cpp | Extra X11 thread for Linux/Solaris; no X11 on Haiku. |
| ipc/glue/BrowserProcessSubThread.h | Same. |
| ipc/glue/MessageLink.cpp | Solaris `std::queue` name clash; not an issue with libstdc++ on Haiku. |
| js/src/builtin/TestingFunctions.cpp | Solaris disables mapped-array-buffer in tests; Haiku mmap works. |
| js/src/ctypes/CTypes.cpp | `<ieeefp.h>` is Solaris-only. |
| js/src/gc/Memory.cpp | Haiku has `madvise(MADV_DONTNEED)`; Solaris high-address mmap hack is not needed. |
| js/src/Makefile.in | SPARC-only flags. |
| js/src/vm/Time.cpp | Solaris `_REENTRANT`/`_SVID_GETTOD` only. |
| js/xpconnect/src/XPCJSContext.cpp | Haiku takes the generic catch-all stack quota (1 MB on 64-bit), which is safe for 256 KB-default secondary threads too. |
| js/xpconnect/src/XPCShellImpl.cpp | Haiku has `setenv`; generic path applies. |
| layout/style/nsRuleNode.cpp | Haiku's `<stdlib.h>` includes `<alloca.h>`. |
| Makefile.in | Symbol store for crash reporter, which is off. |
| media/libaom/moz.build | "Linux, SunOS, etc." config is the right one for x86_64 ELF. |
| media/libcubeb/src/cubeb_sun.c | Sun audio backend; Haiku audio backend belongs to misc. |
| media/libpng/CHANGES | Changelog text. |
| media/libtheora/moz.build | Haiku keeps the x86 asm (Solaris excluded). Compiled in the VM. |
| media/libvorbis/moz.build | `HAVE_ALLOCA_H` not needed; alloca via stdlib.h. Compiled in the VM. |
| memory/mimalloc/src/static.c | mimalloc is not used. |
| memory/mozjemalloc/jemalloc.c | jemalloc is disabled on Haiku. |
| modules/libjar/nsZipArchive.cpp | Haiku has `madvise(MADV_WILLNEED)`; XP_UNIX path applies. |
| modules/zlib/src/ChangeLog | Changelog text (and system zlib is used). |
| netwerk/wifi/moz.build | necko-wifi disabled. |
| python/altgraph/doc/_build/doctrees/environment.pickle | Binary doc artefact. |
| python/macholib/doc/_build/doctrees/environment.pickle | Binary doc artefact. |
| python/mozbuild/mozbuild/action/generate_symbols_file.py | Haiku uses the GNU ld version-script branch. |
| python/mozbuild/mozbuild/frontend/gyp_reader.py | Solaris LDFLAGS passthrough; gyp OS is mapped in gyp_base.mozbuild (haiku-config). |
| python/mozbuild/mozbuild/mozconfig.py | `/bin/sh` on Haiku is bash. |
| toolkit/components/osfile/modules/osfile_unix_back.jsm | Generic code already handles `d_name[1]` and missing `d_type` (Haiku's dirent); libroot naming done on haiku-misc. |
| toolkit/components/protobuf/src/google/protobuf/stubs/atomicops.h | GCC atomics path applies. |
| toolkit/components/protobuf/src/google/protobuf/stubs/platform_macros.h | Same. |
| toolkit/components/terminator/nsTerminator.cpp | Solaris tick-unit quirk only. |
| toolkit/library/dependentlibs.py | ELF + readelf path applies. |
| toolkit/library/libxul.mk | Linux/Solaris gdb autoload and PT_LOAD checks are optional. |
| toolkit/mozapps/update/common/updatedefines.h | Updater disabled. |
| toolkit/mozapps/update/updater/updater.cpp | Updater disabled. |
| toolkit/xre/nsSigHandlers.cpp | FPU handler bodies are Linux/Solaris-specific and FP exceptions are masked by default; Haiku's soft fd limit is fine. |
| xpcom/base/nsDebugImpl.cpp | GCC x86_64 `int $3` branch applies. |
| xpcom/ds/nsMathUtils.h | `<ieeefp.h>` is Solaris-only. |
| xpcom/glue/FileUtils.cpp | Read-ahead is an optimisation (the BSDs also skip it); no-op on Haiku. |
| xpcom/string/nsTSubstring.h | 32-bit Solaris `pid_t` issue only. |

## Notes for other areas

- `__unix__` is not defined on Haiku: any `#if defined(__unix__)` gate excludes Haiku.
  In first-party/third-party code outside tests: eglplatform.h (fixed), skia SkPreConfig.h
  (haiku-widget), libvpx vp8/common/threading.h (only `thread_sleep`; `sched_yield()` is fine),
  libjxl extras/mmap.cc (not built), mimalloc (not used).
