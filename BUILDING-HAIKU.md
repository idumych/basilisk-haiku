# Building Basilisk on Haiku

For Haiku R1/beta6 x86_64. The port is in progress: the engine and most of the
tree compile; check `BUILD-STATUS.md` for how far the full build gets.

## 1. Packages

```sh
pkgman install -y gcc haiku_devel make perl m4 git zip unzip \
    python3.12 autoconf213 pkgconfig yasm nasm \
    nspr_devel nss_devel libffi_devel zlib_devel bzip2_devel \
    libjpeg_turbo_devel fontconfig_devel freetype_devel \
    noto noto_sans_cjk_jp
```

Only needed if you add the matching `--with-system-*` options:
`icu74_devel libvpx_devel libevent_devel libpng16_devel harfbuzz_devel`.

All of these come from the Haiku and HaikuPorts repositories that a fresh
install already has. GTK is not needed: the build uses the native `cairo-haiku`
toolkit.

## 2. Source

UXP (the engine) is the `platform` submodule:

```sh
mkdir -p /boot/home/src && cd /boot/home/src
git clone https://github.com/idumych/basilisk-haiku.git basilisk
cd basilisk
git checkout haiku-all
git submodule update --init platform
```

`haiku-all` is the integration branch; the submodule commit it records is the
matching UXP branch.

## 3. mozconfig

Use `mozconfig-haiku` from the repository root. It sets the objdir to
`/boot/home/work/config/obj`; change that line to suit you, for example:

```sh
sed 's#^mk_add_options MOZ_OBJDIR=.*#mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-haiku#' \
    mozconfig-haiku > mozconfig
```

Useful additions:
- `ac_add_options --disable-debug-symbols` makes objects ~3x smaller and links
  much faster.
- `ac_add_options --enable-js-shell` also builds `dist/bin/js`, for the engine
  tests below.

## 4. Build

Run mach with Python 3.12, from the Basilisk root:

```sh
export MOZCONFIG=$PWD/mozconfig
python3.12 platform/mach configure
python3.12 platform/mach build
```

`mozconfig-haiku` uses `-j6`; set `mk_add_options MOZ_MAKE_FLAGS=-jN` for your
CPU count.

## Resources

- Disk: about 1.5 GB of source and 5-8 GB of objdir with
  `--disable-debug-symbols`. Debug symbols take several times more (the
  standalone js engine alone is a 680 MB static library with them).
  Keep 20 GB free.
- RAM: 16 GB is comfortable; linking libxul with gcc needs several GB.
- Time: configure and the export step take minutes; the full compile takes
  hours, mostly in dom/, layout/ and the third-party libraries.

## Gotchas

- **`python3` is 3.14** on beta6 and the build system doesn't run with it. Always
  use `python3.12 platform/mach ...`. The mozconfig exports `PYTHON3` for the
  sub-tools.
- **Clock skew.** If the system clock is behind file timestamps (common after
  copying a tree from another machine or a VM), make stops with "configure is
  out of date" or loops regenerating files. Touch the tree to the current time
  (`find . -newer /tmp/now -exec touch {} +` after `touch /tmp/now`); don't
  future-date `config.status`.
- **No `patch`.** Haiku has no `patch` tool; apply diffs with
  `git apply --directory=platform` (or plain `git apply` inside `platform/`).
- **Shared VM or slow disk.** Creating many small files on BFS is slow;
  streaming a tree with `tar` is much faster than `cp -a` or `rsync`.
- Most Haiku specifics are behind `XP_HAIKU` (C/C++) and `MOZ_WIDGET_HAIKU`
  (toolkit), with `XP_UNIX` also defined.

## Engine tests

With `--enable-js-shell` (or a standalone js build), run SpiderMonkey's
jit-tests in Haiku:

```sh
sh packaging/haiku/run-engine-tests.sh OBJDIR [platform-dir] [test dirs...]
```

The default test subset is `basic ion asm.js sunspider` in three modes
(default, `--ion-eager`, interpreter only). Known failures are listed in
`packaging/haiku/jit-test-expected-failures.txt`; the script exits 0 when only
those fail. If `xpcshell` was built (`--enable-tests`), it also runs a quick
xpcshell check.

A standalone engine build, for quicker work on SpiderMonkey:

```sh
mkdir -p /boot/home/work/js-obj && cd /boot/home/work/js-obj
# configure.py regenerates old-configure from old-configure.in itself
OLD_CONFIGURE=/path/to/platform/js/src/old-configure \
    python3.12 /path/to/platform/configure.py --enable-project=js \
    --enable-optimize --disable-debug --disable-jemalloc \
    --enable-posix-nspr-emulation --disable-shared-js --disable-debug-symbols
make -j6
```
