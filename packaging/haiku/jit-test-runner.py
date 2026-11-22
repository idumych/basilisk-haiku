#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Minimal Python 3 runner for SpiderMonkey's jit-tests. UXP's own harness
# (js/src/jit-test/jit_test.py) is Python 2 era and doesn't run on Haiku's
# Python 3. This follows the same rules as js/src/tests/lib/jittests.py for
# the |jit-test| directives that matter here.
#
# usage: jit-test-runner.py JS_SHELL JIT_TEST_DIR [-j N] [--expected FILE] DIR_OR_TEST...

import argparse, os, subprocess, sys, tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
ap.add_argument('js')
ap.add_argument('jit_test_dir', help='js/src/jit-test in the source tree')
ap.add_argument('tests', nargs='+', help='directories or files under tests/')
ap.add_argument('-j', type=int, default=4)
ap.add_argument('--timeout', type=int, default=150)
ap.add_argument('--expected', help='file of tests expected to fail')
ap.add_argument('--modes', default='default,ion-eager,interp')
args = ap.parse_args()

TESTS = os.path.join(args.jit_test_dir, 'tests')
LIB = os.path.join(args.jit_test_dir, 'lib')
MODES = {
    'default': [],
    'ion-eager': ['--ion-eager', '--ion-offthread-compile=off'],
    'baseline-eager': ['--baseline-eager'],
    'interp': ['--no-baseline', '--no-ion'],
}
modes = [(m, MODES[m]) for m in args.modes.split(',')]
cache_dir = tempfile.mkdtemp(prefix='jit-test-cache-')

def collect(paths):
    out = []
    for p in paths:
        full = os.path.join(TESTS, p)
        if os.path.isfile(full):
            out.append(full)
            continue
        for root, _, files in os.walk(full):
            out += [os.path.join(root, f) for f in sorted(files) if f.endswith('.js')]
    return out

def meta(path):
    m = {'error': None, 'status': 0, 'flags': [], 'skip': None, 'crash': False,
         'oom': False, 'tz': False}
    with open(path, encoding='utf-8', errors='replace') as f:
        first = f.readline()
    i = first.find('|jit-test|')
    if i < 0:
        return m
    for part in first[i + 10:].split(';'):
        part = part.strip()
        if not part:
            continue
        key, _, val = part.partition(':')
        key, val = key.strip(), val.strip()
        if key == 'error':
            m['error'] = val
        elif key == 'exitstatus':
            m['status'] = int(val)
        elif key == 'crash':
            m['crash'] = True
        elif key == 'allow-oom':
            m['oom'] = True
        elif key == 'tz-pacific':
            m['tz'] = True
        elif key == 'slow':
            m['skip'] = 'slow'
        elif key == 'module':
            m['skip'] = 'module'
        elif key == 'skip-if':
            m['skip'] = 'skip-if'
        elif key.startswith('--'):
            m['flags'].append(key if not val else '%s=%s' % (key, val))
    return m

def run(job):
    path, (mode, flags) = job
    m = meta(path)
    if m['skip']:
        return ('SKIP', path, mode, m['skip'])
    expr = ("const platform='%s'; const libdir='%s/'; const scriptdir='%s/'"
            % (sys.platform, LIB, os.path.dirname(path)))
    cmd = ([args.js, '--js-cache', cache_dir] + flags + m['flags'] +
           ['-f', os.path.join(LIB, 'prologue.js'), '-e', expr, '-f', path])
    env = dict(os.environ)
    if m['tz']:
        env['TZ'] = 'PST8PDT'
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=args.timeout, env=env)
    except subprocess.TimeoutExpired:
        return ('TIMEOUT', path, mode, '')
    out = (p.stdout + p.stderr).decode('utf-8', 'replace')
    rc = p.returncode
    if m['error']:
        ok = rc == 3 and m['error'] in out
    elif m['crash']:
        ok = rc != 0
    else:
        ok = rc == m['status'] or (m['oom'] and 'out of memory' in out)
    if 'Assertion failed:' in out and not m['error']:
        ok = False
    tail = '' if ok else 'rc=%d %s' % (rc, out[-300:].replace('\n', ' | '))
    return ('PASS' if ok else 'FAIL', path, mode, tail)

tests = collect(args.tests)
jobs = [(t, mode) for t in tests for mode in modes]
with ThreadPoolExecutor(args.j) as pool:
    results = list(pool.map(run, jobs))

expected = set()
if args.expected and os.path.exists(args.expected):
    with open(args.expected) as f:
        expected = {l.split('#')[0].strip() for l in f if l.split('#')[0].strip()}

unexpected = 0
for status, path, mode, info in results:
    rel = os.path.relpath(path, TESTS)
    if status in ('FAIL', 'TIMEOUT'):
        known = rel in expected
        unexpected += 0 if known else 1
        print('%s%s %s [%s] %s' % ('KNOWN-' if known else '', status, rel, mode, info))
counts = Counter(r[0] for r in results)
print('SUMMARY tests=%d runs=%d %s unexpected=%d' %
      (len(tests), len(jobs), dict(counts), unexpected))
sys.exit(1 if unexpected else 0)
