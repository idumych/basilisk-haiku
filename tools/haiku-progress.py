#!/usr/bin/env python3
"""Measure how much of UXP has been adapted to Haiku, redraw the README's
progress bar, commit it on the `haiku` branch and push everything to GitHub.

The measure: UXP's Solaris port is the most recent Unix port, so every file
that had to learn about Solaris is a place a new OS needs. We count those
files (on upstream `master`, minus third-party code Haiku replaces with system
libraries and code that isn't built) and how many of them mention Haiku on any
`haiku-*` branch.

Run by the post-commit / post-merge hooks of both repositories (in the
background, serialised by a lock), or by hand: tools/haiku-progress.py [--no-push]
"""
import fcntl, os, re, subprocess, sys

TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UXP = os.path.join(TOP, "platform")
BRANCHES = ["haiku-config", "haiku-js", "haiku-xpcom", "haiku-ipc", "haiku-widget", "haiku-misc"]
SOLARIS = r"XP_SOLARIS|SunOS|__sun\b|SOLARIS"
HAIKU = r"XP_HAIKU|__HAIKU__|MOZ_WIDGET_HAIKU|OS_HAIKU|[Hh]aiku"
# Replaced by system libraries, not built for Basilisk, or not code.
EXCLUDE = ["nsprpub", "security/nss", "intl/icu", "media/webrtc", "testing", "**/tests/**",
           "**/test/**", "ldap", "mailnews", "python/psutil", "js/src/ctypes/libffi",
           "other-licenses", "third_party/python", "build/pgo", "**/*.html", "**/*.txt",
           "**/*.md", "**/*.rst"]
README = os.path.join(TOP, "README.md")
BEGIN, END = "<!-- haiku-progress:begin -->", "<!-- haiku-progress:end -->"


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and r.returncode not in (0, 1):  # 1 = git grep found nothing
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr}")
    return r.stdout


def grep_files(repo, pattern, ref, paths):
    out = git(repo, "grep", "-lE", pattern, ref, "--", *paths)
    return {line.split(":", 1)[1] for line in out.splitlines() if ":" in line}


def measure():
    targets = sorted(grep_files(UXP, SOLARIS, "master", ["."] + [":!" + e for e in EXCLUDE]))
    done = set()
    for b in BRANCHES:
        done |= grep_files(UXP, HAIKU, b, targets) & set(targets)
    return len(done), len(targets)


def svg(done, total):
    pct = round(100 * done / total) if total else 0
    w, h, bar = 480, 28, 300
    fill = round(bar * done / total) if total else 0
    label = f"{done} / {total} files ({pct}%)"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" role="img" aria-label="Haiku support: {label}">
<title>Haiku support: {label}</title>
<rect width="{w}" height="{h}" rx="5" fill="#2b2b2b"/>
<rect x="6" y="6" width="{bar}" height="{h-12}" rx="3" fill="#555"/>
<rect x="6" y="6" width="{fill}" height="{h-12}" rx="3" fill="#ffcb00"/>
<text x="{bar+16}" y="{h/2+5}" font-family="DejaVu Sans,Verdana,sans-serif" font-size="13" fill="#fff">{label}</text>
</svg>
"""


def update(push):
    done, total = measure()
    name = f"progress-{done}-{total}.svg"
    os.makedirs(os.path.join(TOP, "docs"), exist_ok=True)
    for f in os.listdir(os.path.join(TOP, "docs")):  # fixed names get stale behind GitHub's image cache
        if re.fullmatch(r"progress-\d+-\d+\.svg", f) and f != name:
            os.remove(os.path.join(TOP, "docs", f))
    with open(os.path.join(TOP, "docs", name), "w") as fh:
        fh.write(svg(done, total))
    block = (f"{BEGIN}\n![Haiku support: {done} of {total} files](docs/{name})\n\n"
             f"**{done} of {total}** platform-specific files in UXP handle Haiku. These are the files "
             f"UXP's Solaris port had to change, so a new OS needs them too (system-library and unbuilt "
             f"code excluded). Counted across all `haiku-*` branches by "
             f"[`tools/haiku-progress.py`](tools/haiku-progress.py) on every commit. It measures source "
             f"coverage, not whether the browser works: see the status table.\n{END}")
    text = open(README).read()
    text = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), lambda m: block, text, flags=re.S)
    open(README, "w").write(text)

    git(TOP, "add", "-A", "README.md", "docs")
    if subprocess.run(["git", "-C", TOP, "diff", "--cached", "--quiet"]).returncode == 0:
        print(f"progress unchanged: {done}/{total}")
    else:
        env = dict(os.environ, HAIKU_PROGRESS="1")
        subprocess.run(["git", "-C", TOP, "commit", "-q", "-m",
                        f"Haiku: progress {done}/{total}\n\n"
                        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], env=env, check=True)
        print(f"progress updated: {done}/{total}")
    if push:
        refs = ["haiku"] + BRANCHES
        for repo in (UXP, TOP):
            r = subprocess.run(["git", "-C", repo, "push", "-q", "github", *refs],
                               capture_output=True, text=True)
            if r.returncode:
                print(f"push failed in {repo}: {r.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    if os.environ.get("HAIKU_PROGRESS"):  # our own commit: don't recurse
        sys.exit(0)
    with open(os.path.join(TOP, ".git", "haiku-progress.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        update(push="--no-push" not in sys.argv)
