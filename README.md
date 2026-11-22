# Basilisk for Haiku (work in progress)

A community port of the [Basilisk](https://www.basilisk-browser.org/) web browser to
[Haiku](https://www.haiku-os.org/), with a native Haiku user interface (BWindow/BView).
Basilisk's lead developer has
[given the Haiku community permission](https://discuss.haiku-os.org/t/port-basilisk-browser-to-haiku/16046)
to use the official Basilisk branding for this port and to ignore the static-library
requirements. This is not an official Basilisk build.

Basilisk keeps its engine, UXP, in the `platform` submodule. The Haiku changes to it live in
[idumych/uxp-haiku](https://github.com/idumych/uxp-haiku).

## Progress

<!-- haiku-progress:begin -->
![Basilisk on Haiku: 4 of 11 milestones](docs/progress-4-11-20261122011945.svg)

Milestones towards a working browser, ticked only with verified evidence ([`tools/milestones.txt`](tools/milestones.txt)):

- [x] configure passes on Haiku R1/beta6 (config.status in the VM: OS_ARCH=Haiku, MOZ_WIDGET_TOOLKIT=haiku)
- [x] every area compiles on its own (per-area objdirs in the VM: js, xpcom, ipc, widget, media/netwerk/toolkit, layout/dom)
- [x] the JavaScript engine runs and passes its tests (js shell: 6,684 of 6,735 jit-test runs pass, 0 unexpected)
- [x] the merged full build compiles without errors (haiku-all build in the VM: every file compiles, 0 compile errors (link errors only))
- [ ] libxul links
- [ ] Basilisk starts and stays running
- [ ] a browser window appears and draws
- [ ] a local web page renders correctly
- [ ] an HTTPS site loads
- [ ] an .hpkg of the real build installs and passes the package checks
- [ ] the release test plan passes on Haiku R1/beta6

Source coverage, for reference: of the 114 files UXP's Solaris port had to change, 42 now handle Haiku and 71 were reviewed and need nothing ([SOLARIS-AUDIT.md](https://github.com/idumych/basilisk-haiku/blob/haiku-config/SOLARIS-AUDIT.md)). That says the source is adapted, not that the browser works.
<!-- haiku-progress:end -->

## Status (November 2026)

| Part | State |
|---|---|
| Build system (`configure`, `cairo-haiku` toolkit, system NSPR/NSS) | **configure passes** on Haiku; full build in progress |
| SpiderMonkey (JS engine) | **builds and runs** on Haiku R1/beta6 x86_64: 6,684 of 6,735 jit-test runs pass (the 15 failures are 5 stale tests, same in every mode); JIT, asm.js, Intl, js-ctypes; time zone and language from Haiku's locale settings |
| XPCOM, mozglue, memory, mfbt | **compiles** on Haiku (not linked yet): xptcall, file and directory services, memory reporters, Tracker/BRoster for reveal and launch |
| IPC (Chromium layer) | **compiles** on Haiku (not linked yet): fork/exec child processes, system libevent, Haiku thread names |
| Native UI (`widget/haiku`, gfx platform) | **compiles** on Haiku (not linked yet): app shell, windows, painting, clipboard, file picker, keyboard; native control look (BControlLook), drag and drop, image clipboard, file filters, multiple screens, basic IME |
| Media, networking, toolkit | **compile** on Haiku (not linked yet): all media decoders, audio through the Media Kit (BSoundPlayer; plays a test tone in the VM), network status from BNetworkRoster, app startup, toolkit components |
| Layout, DOM, parser, image, storage, docshell, editor, intl | **compile** on Haiku (not linked yet) |
| Haiku integration | written, compiles: Command-key shortcuts, Haiku notifications, downloads typed with BEOS:TYPE and META:url, default-browser setting, Tracker icons, single launch, printing via BPrintJob, Noto fonts |
| Media | VP8/VP9/AV1/Opus bundled; H.264/AAC through Haiku's system FFmpeg (libraries load in the VM); WebGL through OSMesa (software) |
| The browser as a whole | every area compiles on its own; the merged full build (`haiku-all`) is compiling, not linked yet |

## Branches

Work happens on one branch per area, in both repositories:
`haiku-config`, `haiku-js`, `haiku-xpcom`, `haiku-ipc`, `haiku-widget`, `haiku-misc`,
and `haiku-all` merges them all for the full build.
`haiku` is the common base; `master` tracks upstream.

## Building

See [BUILDING-HAIKU.md](https://github.com/idumych/basilisk-haiku/blob/haiku-all/BUILDING-HAIKU.md) on the `haiku-all` branch:
the HaikuPorts packages to install, the mozconfig, the build commands, and the gotchas we hit
(Haiku R1/beta6 x86_64; about 16 GB RAM and 10 GB disk). The full browser does not link yet.

Licence: MPL 2.0, as upstream.

---

## Upstream Basilisk README

This is the source code for the Basilisk web browser, an independent browser
derived from Firefox/Mozilla community code. The source tree is laid out in a
"comm-central" style configuration where only the code specific to Basilisk is
kept in this repository.

The shared Unified XUL Platform source code is referenced here as a git
submodule contained in the `platform` directory and is required to build the
application.

## Getting the platform sub-module
`git submodule init && git submodule update`

## Documentation
See the [Basilisk Wiki](https://repo.palemoon.org/Basilisk-Dev/Basilisk/wiki) for information regarding building Basilisk.

## Resources

 * [Basilisk home page](http://www.basilisk-browser.org/)
 * [Basilisk Development Team Code of Conduct](https://repo.palemoon.org/Basilisk-Dev/Basilisk/src/branch/master/CODE_OF_CONDUCT.md)
 * [UXP Code of Conduct, Contributing, and UXP Coding style](https://repo.palemoon.org/MoonchildProductions/UXP/src/branch/master/docs)
