## Basilisk @VERSION@ for Haiku (unofficial community port)

Basilisk is a XUL-based web browser built on the Unified XUL Platform (UXP).
This package is an **unofficial community port to Haiku**. It is not made or
supported by the Basilisk developers: please report problems to the Haiku
port, not to the Basilisk project. The Basilisk name and branding are used
with the permission of Basilisk's lead developer: https://discuss.haiku-os.org/t/port-basilisk-browser-to-haiku/16046 (December 2024: permission to use the official Basilisk branding for the Haiku port and to use system libraries instead of the static-library requirements)

### Downloads
| Platform | File |
|---|---|
| Haiku R1/beta6 x86_64 (also installs on Renku OS) | `basilisk-@VERSION@-@REVISION@-x86_64.hpkg` |

Linux: not part of this release. Basilisk has its own official Linux (and
Windows/macOS) builds at https://www.basilisk-browser.org/; this port only
adds Haiku.

### Install
Haiku R1/beta6: `pkgman install ./basilisk-@VERSION@-@REVISION@-x86_64.hpkg`
Optional packages, used when installed:
- `pkgman install mesa` for WebGL (software rendering)
- `pkgman install ffmpeg6` (or `ffmpeg8`) for H.264 video and AAC audio;
  VP8, VP9, AV1 and Opus play without it

### Tested
<!-- One line per platform, from the evidence `os:` lines. Fill in only what was run. -->
- Haiku R1/beta6 x86_64 (hrev________): ________
- Renku OS x86_64 (________): ________

Not tested: ________

### Known gaps
- WebGL is software-rendered (OSMesa/llvmpipe) and needs the optional `mesa`
  package; no hardware acceleration.
- H.264/AAC media need the optional ffmpeg6/ffmpeg8 package.
- No multi-process (e10s); content runs in the main process. No NPAPI plugins.
- Input methods: basic support only (dead keys and simple composition; full
  CJK IME not verified).
- No crash reporter, no built-in updater: update with pkgman.
- Accessibility (screen readers) is not wired up for the native Haiku widget yet.
- Some form controls fall back to the default CSS look in vertical writing modes;
  menu check/radio marks use the default look.

### Checksums
See SHA256SUMS.
