# Basilisk for Haiku (work in progress)

A community port of the [Basilisk](https://www.basilisk-browser.org/) web browser to
[Haiku](https://www.haiku-os.org/), with a native Haiku user interface (BWindow/BView).
Basilisk's lead developer has
[given the Haiku community permission](https://discuss.haiku-os.org/t/port-basilisk-browser-to-haiku/16046)
to use the official Basilisk branding for this port and to ignore the static-library
requirements. This is not an official Basilisk build.

Basilisk keeps its engine, UXP, in the `platform` submodule. The Haiku changes to it live in
[idumych/uxp-haiku](https://github.com/idumych/uxp-haiku).

## Status (November 2026)

| Part | State |
|---|---|
| Build system (`configure`, `cairo-haiku` toolkit, system NSPR/NSS) | in progress |
| SpiderMonkey (JS engine) | **builds and runs** on Haiku R1/beta6 x86_64: JIT, asm.js, Intl, js-ctypes |
| XPCOM, mozglue, memory | ported in source, not compiled yet |
| IPC (Chromium layer) | ported in source, not compiled yet |
| Native UI (`widget/haiku`, gfx platform) | written (~5,000 lines, adapted from HaikuPorts' Firefox port), not compiled yet |
| Media, networking, toolkit | ported in source, not compiled yet |
| The browser as a whole | does not build yet |

## Branches

Work happens on one branch per area, in both repositories:
`haiku-config`, `haiku-js`, `haiku-xpcom`, `haiku-ipc`, `haiku-widget`, `haiku-misc`.
`haiku` is the common base; `master` tracks upstream.

## Building

Target: Haiku R1/beta6 x86_64 with HaikuPorts packages (`gcc`, `haiku_devel`, `python3.12`,
`autoconf213`, `yasm`, `nspr_devel`, `nss_devel`, `libevent_devel`, `libffi_devel`, `icu74_devel`,
`libvpx_devel`, `fontconfig_devel`, `freetype_devel`). A `mozconfig-haiku` will be on the
`haiku-config` branch once the full build configures.

Licence: MPL 2.0, as upstream.
