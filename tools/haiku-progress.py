#!/usr/bin/env python3
"""Redraw the README's progress bar from tools/milestones.txt (plus a source-coverage line), commit it on the `haiku` branch and push everything to GitHub.

The measure: UXP's Solaris port is the most recent Unix port, so every file
that had to learn about Solaris is a place a new OS needs. We count those
files (on upstream `master`, minus third-party code Haiku replaces with system
libraries and code that isn't built) and how many of them mention Haiku on any
`haiku-*` branch.

Run by the post-commit / post-merge hooks of both repositories (in the
background, serialised by a lock), or by hand: tools/haiku-progress.py [--no-push]
"""
import fcntl, os, re, subprocess, sys, time

TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UXP = os.path.join(TOP, "platform")
BRANCHES = ["haiku-config", "haiku-js", "haiku-xpcom", "haiku-ipc", "haiku-widget", "haiku-misc", "haiku-all"]
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


def reviewed_files():
    """Files the audit (SOLARIS-AUDIT.md on Basilisk haiku-config) found need nothing for Haiku."""
    text = git(TOP, "show", "haiku-config:SOLARIS-AUDIT.md", check=False)
    section = text.split("## Nothing needed", 1)[1] if "## Nothing needed" in text else ""
    section = section.split("\n## ", 1)[0]
    return {m.group(1).strip() for m in re.finditer(r"^\|\s*([^|]+?)\s*\|", section, re.M)} - {"File", "---"}


def measure():
    targets = sorted(grep_files(UXP, SOLARIS, "master", ["."] + [":!" + e for e in EXCLUDE]))
    done = set()
    for b in BRANCHES:
        done |= grep_files(UXP, HAIKU, b, targets) & set(targets)
    reviewed = (reviewed_files() & set(targets)) - done
    return len(done), len(reviewed), len(targets)


def milestones():
    """(done, text, evidence) for each line of tools/milestones.txt."""
    out = []
    for line in open(os.path.join(TOP, "tools", "milestones.txt")):
        if line.startswith("#") or not line.strip():
            continue
        mark, text, evidence = (line.rstrip("\n").split("|") + ["", ""])[:3]
        out.append((mark.strip() == "x", text.strip(), evidence.strip()))
    return out


def svg(steps):
    done, total = sum(d for d, _, _ in steps), len(steps)
    w, h, seg, gap = 560, 28, 22, 3
    label = f"{done} of {total} milestones"
    boxes = "".join(f'<rect x="{6 + i * (seg + gap)}" y="6" width="{seg}" height="{h-12}" rx="3" '
                    f'fill="{"#ffcb00" if d else "#555"}"/>' for i, (d, _, _) in enumerate(steps))
    x = 6 + total * (seg + gap) + 10
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" role="img" aria-label="Basilisk on Haiku: {label}">
<title>Basilisk on Haiku: {label}</title>
<rect width="{w}" height="{h}" rx="5" fill="#2b2b2b"/>
{boxes}
<text x="{x}" y="{h/2+5}" font-family="DejaVu Sans,Verdana,sans-serif" font-size="13" fill="#fff">{label}</text>
</svg>
"""


def update(push):
    adapted, reviewed, files = measure()
    steps = milestones()
    done, total = sum(d for d, _, _ in steps), len(steps)
    docs = os.path.join(TOP, "docs")
    os.makedirs(docs, exist_ok=True)
    old = [f for f in os.listdir(docs) if re.fullmatch(r"progress-[\d-]+\.svg", f)]
    current = f"progress-{done}-{total}-"
    image = svg(steps)
    same = len(old) == 1 and old[0].startswith(current) and \
        open(os.path.join(docs, old[0])).read() == image
    if same:
        name = old[0]  # unchanged: keep the image and its name
    else:
        # A new name for every new image: GitHub's README image cache keeps a path for
        # minutes and ignores query strings, so a reused name would show a stale bar.
        name = current + time.strftime("%Y%m%d%H%M%S", time.gmtime()) + ".svg"
        for f in old:
            os.remove(os.path.join(docs, f))
        with open(os.path.join(docs, name), "w") as fh:
            fh.write(image)
    checklist = "\n".join(f"- [{'x' if d else ' '}] {t}" + (f" ({e})" if d and e else "")
                          for d, t, e in steps)
    block = (f"{BEGIN}\n![Basilisk on Haiku: {done} of {total} milestones](docs/{name})\n\n"
             f"Milestones towards a working browser, ticked only with verified evidence "
             f"([`tools/milestones.txt`](tools/milestones.txt)):\n\n{checklist}\n\n"
             f"Source coverage, for reference: of the {files} files UXP's Solaris port had to change, "
             f"{adapted} now handle Haiku and {reviewed} were reviewed and need nothing "
             f"([SOLARIS-AUDIT.md](https://github.com/idumych/basilisk-haiku/blob/haiku-config/SOLARIS-AUDIT.md)). "
             f"That says the source is adapted, not that the browser works.\n{END}")
    text = open(README).read()
    text = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), lambda m: block, text, flags=re.S)
    open(README, "w").write(text)

    git(TOP, "add", "-A", "README.md", "docs")
    if subprocess.run(["git", "-C", TOP, "diff", "--cached", "--quiet"]).returncode == 0:
        print(f"progress unchanged: {done}/{total} milestones")
    else:
        env = dict(os.environ, HAIKU_PROGRESS="1")
        subprocess.run(["git", "-C", TOP, "commit", "-q", "-m",
                        f"Haiku: progress {done}/{total} milestones\n\n"
                        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], env=env, check=True)
        print(f"progress updated: {done}/{total} milestones")
    if push:
        refs = ["haiku"] + BRANCHES
        # The app repo's GitHub remote is "origin" (upstream Basilisk is "upstream");
        # the engine repo's GitHub remote is still "github".
        for repo, remote in ((UXP, "github"), (TOP, "origin")):
            r = subprocess.run(["git", "-C", repo, "push", "-q", remote, *refs],
                               capture_output=True, text=True)
            if r.returncode:
                print(f"push failed in {repo}: {r.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    if os.environ.get("HAIKU_PROGRESS"):  # our own commit: don't recurse
        sys.exit(0)
    with open(os.path.join(TOP, ".git", "haiku-progress.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        update(push="--no-push" not in sys.argv)
