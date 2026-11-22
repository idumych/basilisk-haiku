#!/bin/sh
# run-engine-tests.sh: run INSIDE Haiku. Runs SpiderMonkey jit-tests against
# the js shell of a build, and a quick xpcshell check if xpcshell was built.
#
# Usage:
#   sh packaging/haiku/run-engine-tests.sh OBJDIR [SRCDIR] [TEST_DIR...]
#
#   OBJDIR    objdir with dist/bin/js (browser builds need
#             `ac_add_options --enable-js-shell`; a standalone js build has it)
#   SRCDIR    platform/ (UXP) source dir; default: the topsrcdir recorded in
#             OBJDIR/config.status
#   TEST_DIR  jit-test dirs under js/src/jit-test/tests
#             (default: basic ion asm.js sunspider)
#
# Environment:
#   JOBS=4                    parallel test processes
#   MODES=default,ion-eager,interp   shell flag sets (see jit-test-runner.py)
#   PYTHON=python3.12         Haiku's python3 is 3.14; 3.12 is what the build uses
#
# Exit status: 0 = only known failures (jit-test-expected-failures.txt),
# 1 = unexpected failures, 2 = setup problem.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
OBJDIR=${1:?usage: run-engine-tests.sh OBJDIR [SRCDIR] [TEST_DIR...]}
shift
PYTHON=${PYTHON:-python3.12}
JOBS=${JOBS:-4}
MODES=${MODES:-default,ion-eager,interp}

if [ $# -gt 0 ] && [ -d "$1/js/src/jit-test" ]; then
    SRCDIR=$1
    shift
else
    SRCDIR=$(sed -n "s/^topsrcdir = '\(.*\)'$/\1/p" "$OBJDIR/config.status" 2>/dev/null | head -1)
    # A browser objdir records the Basilisk top dir; the engine is in platform/.
    [ -d "$SRCDIR/platform/js/src/jit-test" ] && SRCDIR=$SRCDIR/platform
fi
[ $# -gt 0 ] || set -- basic ion asm.js sunspider

JS=$OBJDIR/dist/bin/js
JIT_TEST=$SRCDIR/js/src/jit-test
if [ ! -x "$JS" ]; then
    echo "no js shell at $JS (add 'ac_add_options --enable-js-shell' to the mozconfig)" >&2
    exit 2
fi
if [ ! -d "$JIT_TEST/tests" ]; then
    echo "no jit-tests at $JIT_TEST (pass SRCDIR, the platform/ dir)" >&2
    exit 2
fi

echo "== js shell: $JS"
"$JS" -e 'print("print(1+1) = " + (1+1))' || exit 2

STATUS=0
echo "== jit-tests: $* (modes $MODES, $JOBS jobs)"
"$PYTHON" "$HERE/jit-test-runner.py" "$JS" "$JIT_TEST" -j "$JOBS" \
    --modes "$MODES" --expected "$HERE/jit-test-expected-failures.txt" "$@" || STATUS=1

XPCSHELL=$OBJDIR/dist/bin/xpcshell
if [ -x "$XPCSHELL" ]; then
    echo "== xpcshell smoke test"
    OUT=$(cd "$OBJDIR/dist/bin" && ./xpcshell -g . -a . -e '
        Components.utils.import("resource://gre/modules/Services.jsm");
        print("appinfo.OS = " + Services.appinfo.OS);
        print("intl = " + new Intl.DateTimeFormat().resolvedOptions().timeZone);
        print("ok");' 2>&1)
    echo "$OUT"
    case "$OUT" in *ok*) ;; *) STATUS=1 ;; esac
else
    echo "== no xpcshell (needs --enable-tests); skipped"
fi

exit $STATUS
