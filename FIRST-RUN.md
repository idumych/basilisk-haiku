# First run of Basilisk on Haiku: what to check, in order

Run from the host, as soon as `dist/bin/basilisk` links:

    packaging/haiku/smoke-test.sh /boot/home/work/xpcom/obj/dist/bin/basilisk

It starts the browser detached with a fresh profile (`-profile /boot/home/work/smoke-profile
-no-remote`), takes `01-startup.png`, opens a local test page (text, form, checkbox,
select, scrollable div, PNG, colour boxes, a JS line), takes `02-testpage.png`, collects
`app.log` (stdout and stderr with MOZ_LOG for widget/gfx), the syslog tail and any
debug_server report, then quits with `hey Basilisk quit`. If the app doesn't quit, it
kills only that team. The exit code tells you what happened: 0 ok, 2 crash, 3 exited by
itself, 4 hung on quit.

To run it by hand in the VM instead:

    cd /boot/home/work/xpcom/obj/dist/bin
    MOZ_LOG=Widget:4,gfx2d:4,sync ./basilisk -profile /tmp/p -no-remote 2>&1 | tee /tmp/b.log

## Checklist

1. **The process starts and stays up** (more than 10 s). If it exits at once, read
   `app.log`. The usual causes are:
   - "Couldn't load XPCOM" or a missing library: check `LIBRARY_PATH` (not `LD_LIBRARY_PATH`)
     and `dependentlibs.list`. run-mozilla.sh now sets LIBRARY_PATH.
   - `omni.ja` / `greprefs` not found: packaging/`dist/bin` layout, or `GRE_HOME`.
   - XRE_main returns early because no profile is usable: use `-profile` with an empty dir.
2. **A window appears** (`01-startup.png`). If there's no window and no crash, the
   BApplication or BWindow never ran or was never shown. Look at widget/haiku nsAppShell
   (is the BApplication thread running and is the Gecko event loop being pumped?) and
   nsWindow::Show.
3. **It paints.** A grey or black window usually means the compositor gives
   nothing to the BView: basic layers are set up, but the draw target or BBitmap blit in
   widget/haiku (HaikuWindowBuffer/HaikuView) isn't happening, or the stride or format is
   wrong (BGRA32 vs B_RGB32). Colours swapped: wrong surface format. Garbage: wrong stride.
4. **Chrome UI draws** (tabs, URL bar, menus). Missing icons or text: fonts
   (gfxPlatformHaiku and fontconfig; check `fc-list`) or theme images (nsLookAndFeel and the
   native theme).
5. **The test page** (`02-testpage.png`): the text is readable, Ü/ï render, the image shows
   "image OK", the three colour boxes are red, green and blue, and "JavaScript: OK, <UA>"
   is shown. If the JS line still says "not run", the JS engine didn't run the script.
6. **Input:** click into the URL bar and type with the qemu-vm.sh `type`/`key` commands,
   then press Enter. Check key mapping (HaikuKeyboard), focus and the IME path. Check
   mouse clicks on the checkbox and wheel scrolling in the scrollable div.
7. **Network:** load `http://example.com/`, which needs system NSS, NSPR and libnetwork
   (DNS through res_ninit/getaddrinfo). Then load an `https://` page: certificate
   verification uses mozpkix plus the system NSS.
8. **A clean quit:** File > Quit and `hey Basilisk quit` should both exit without a
   debug_server alert, and nsTerminator mustn't fire.

## Likely first crashes and where to look

On Haiku a crashing app does not die. debug_server holds it, and the app looks hung
with an alert on screen. The smoke test configures debug_server to write a report for
the executable (`~/config/settings/system/debug_server/settings`, `executable_actions`)
and also asks `Debugger --save-report` for the team. Read the report's stack of the
crashing thread first. For a live session use `Debugger --team <id>`.

| Symptom (top of stack) | Likely area / owner |
|---|---|
| `NS_InitXPCOM` / component registration, `nsComponentManagerImpl` | xpcom: BinaryPath.h (`find_path`/`B_APP_IMAGE_SYMBOL`), SpecialSystemDirectory, `GRE_HOME` |
| `mozilla::TimeStamp`, `PR_*` in early startup | mozglue TimeStamp_posix; system NSPR 4.39 vs the expected API |
| `js::` stack-limit asserts, crash in `JS_Init` or the first GC | js: NativeStack (get_thread_info), gc/Memory.cpp mmap alignment |
| `base::MessagePumpLibevent`, `base::Thread::StartWithOptions` | ipc: libevent on Haiku, pipes and sockets in ipc_channel_posix |
| `ContentParent::LaunchSubprocess` / child dies | ipc + e10s: try `MOZ_FORCE_DISABLE_E10S=1` / `browser.tabs.remote.autostart=false` first |
| `nsAppShell::Init`, `BApplication` asserts (be_app is NULL, "BApplication must be created first") | widget: BApplication thread start order |
| `nsWindow::Create` / `BWindow` / `BView::Draw` | widget: window creation, locking (LockLooper), threading |
| `gfxPlatform::Init`, `gfxPlatformFontList`, FcInit | gfx: fontconfig config, gfxPlatformHaiku, font list |
| `gl::GLContextProvider*`, `CompositorBridge` | gfx: GL must be off (Null provider); force `layers.acceleration.disabled=true` |
| `CubebUtils`, audio init on first page | misc: cubeb Haiku backend; `media.cubeb.backend` |
| `nsSSLIOLayer`, `CertVerifier`, mozpkix | misc + config: system NSS (3.133) vs UXP's NSS 3.90 expectations, mozpkix export |
| `OS.File` / `osfile_unix_back.jsm` ctypes errors in the log | misc: libroot naming, Haiku's dirent and stat |
| Hang on quit, nsTerminator crash after 60 s | threads not joined: IPC IO thread, cache I/O, BApplication not quitting |

Useful prefs for the first runs, in `user.js` in the smoke profile:

    user_pref("browser.tabs.remote.autostart", false);
    user_pref("layers.acceleration.disabled", true);
    user_pref("gfx.webrender.enabled", false);
    user_pref("browser.shell.checkDefaultBrowser", false);
    user_pref("toolkit.startup.max_resumed_crashes", -1);
