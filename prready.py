"""Refuse a pull request built on a stale kit or a stale decomp.

    python prready.py kit       last step before a pull request on ZevyaDev/dqix-decomp-kit
    python prready.py decomp    last step before a pull request on ZevyaDev/dqix-decomp
    python prready.py --hook    Claude Code PreToolUse hook: blocks `gh pr create` until READY

Fetches the published kit and decomp-matching and compares your commits with them. Exit 0: READY.
1: NOT READY, one line per problem saying what to do. 2: a fetch failed, or the hook blocked.
"""
import json
import os
import re
import subprocess
import sys

os.environ["DQIX_NO_FRESHNESS"] = "1"
import delinked
import kitpaths

KIT, REPO = kitpaths.KIT, kitpaths.REPO
MATCH_PATHS = ("src/", "include/", "config/")
SOURCE = (".c", ".cpp", ".s")
ADDR = re.compile(r"\b(02[0-9a-fA-F]{6})\b")
SYMBOLS = re.compile(r"^config/([^/]+)/(.+/symbols\.txt)$")
MARKER = re.compile(r"(?m)^(<{7}|>{7})( |\r?$)")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def published(repo, url, branch):
    if git(repo, "fetch", "-q", url, branch).returncode != 0:
        print(f"FETCH FAILED {url} {branch} in {repo}", file=sys.stderr)
        sys.exit(2)
    return git(repo, "rev-parse", "FETCH_HEAD").stdout.strip()


def behind(repo, tip):
    return int(git(repo, "rev-list", "--count", f"HEAD..{tip}").stdout.strip() or 0)


def show(repo, rev, path):
    return git(repo, "show", f"{rev}:{path}").stdout


def delinks(repo, rev, root):
    names = git(repo, "ls-tree", "-r", "--name-only", rev, root).stdout.split()
    return [show(repo, rev, n) for n in names if n.endswith("delinks.txt")]


def diff_lines(repo, tip, path, sign):
    out = git(repo, "diff", "-U0", f"{tip}...HEAD", "--", path).stdout.splitlines()
    return [l[1:] for l in out if l.startswith(sign) and not l.startswith(sign * 3)]


def names(text):
    return {l.split()[0] for l in text.splitlines() if l.strip()}


def existing_regional_binding(name, before, after, other_before, other_after):
    """A raw JPN label can be corrected to an unchanged regional entity."""
    label = re.fullmatch(r"((data|func)_(?:ov\d{3}_)?)([0-9a-f]{8})", name)
    if not label:
        return False
    kind = "kind:data(" if label.group(2) == "data" else "kind:function("
    rows = lambda text: [p for l in text.splitlines() if len(p := l.split()) >= 3]
    old = [r for r in rows(before) if r[0] == name]
    if (len(old) != 1 or not old[0][1].startswith(kind)
            or (label.group(2) == "data" and old[0][2] != "addr:0x" + label.group(3))):
        return False
    replacement = [r for r in rows(after) if r[2] == old[0][2]]
    if len(replacement) != 1 or replacement[0][1:] != old[0][1:]:
        return False
    target = replacement[0][0]
    if ((not re.fullmatch(re.escape(label.group(1)) + r"[0-9a-f]{8}", target)
            and not (label.group(2) == "func" and re.fullmatch(r"_Z[A-Za-z0-9_]+", target)))
            or target in names(before)):
        return False
    old_other = [r for r in rows(other_before) if r[0] == name]
    target_other = [r for r in rows(other_before) if r[0] == target]
    return (len(old_other) == len(target_other) == 1
            and all(r[1].startswith(kind) for r in old_other + target_other)
            and old_other[0][2] != target_other[0][2]
            and [r for r in rows(other_after) if r[0] == name] == old_other
            and [r for r in rows(other_after) if r[0] == target] == target_other)


def staleness():
    problems = []
    kit_tip = published(KIT, kitpaths.KIT_URL, kitpaths.KIT_BRANCH)
    n = behind(KIT, kit_tip)
    if n:
        problems.append(f"KIT BEHIND by {n} commit(s): run python kit_update.py, re-run selfcheck.py and "
                        "regress.py, re-gate what you changed")
    decomp_tip = published(REPO, kitpaths.DECOMP_URL, kitpaths.DECOMP_BRANCH)
    n = behind(REPO, decomp_tip)
    if n:
        problems.append(f"DECOMP BEHIND by {n} commit(s): in {REPO} run git pull --rebase "
                        f"{kitpaths.DECOMP_URL} {kitpaths.DECOMP_BRANCH}, then python tools/configure.py usa "
                        "&& ninja check")
    return problems, kit_tip, decomp_tip


def kit(kit_tip, decomp_tip):
    problems = []
    if git(KIT, "diff", "--name-only", f"{kit_tip}...HEAD", "--", "worker_src/deadends.md").stdout.strip():
        problems.append("NO DEAD ENDS: the kit takes no worker_src/deadends.md change; record the miss in $SP "
                        "(blocker.py, the handoff) and open the pull request from a branch without it")
    matched = delinks(REPO, decomp_tip, "config/usa/arm9")
    cited = dict.fromkeys(a.lower() for l in diff_lines(KIT, kit_tip, "worker_src/core.md", "+") for a in ADDR.findall(l))
    for addr in cited:
        if not delinked.covers(int(addr, 16), matched):
            problems.append(f"UNPROVEN CITATION {addr} in core.md: not matched on {kitpaths.DECOMP_BRANCH}; "
                            "land the match first or cite a landed address")
    return problems


def decomp(decomp_tip):
    problems = []
    changed = git(REPO, "diff", "--name-only", f"{decomp_tip}...HEAD").stdout.split()
    for path in changed:
        if not path.startswith(MATCH_PATHS):
            problems.append(f"OUTSIDE A MATCH {path}: differs from {kitpaths.DECOMP_BRANCH}; restore it with "
                            f"git checkout {decomp_tip[:10]} -- {path}, or send it as its own pull request")
        elif MARKER.search(show(REPO, "HEAD", path)):
            problems.append(f"CONFLICT MARKERS in {path}")
    wired = "\n".join(delinks(REPO, "HEAD", "config"))
    added = git(REPO, "diff", "--name-only", "--diff-filter=A", f"{decomp_tip}...HEAD", "--", "src").stdout.split()
    for path in added:
        if path.endswith(SOURCE) and f"{path}:" not in wired:
            problems.append(f"DEAD FILE {path}: no delinks.txt entry names it; delete it")
    regions = [p.rstrip("/").split("/")[-1] for p in git(REPO, "ls-tree", "-d", "--name-only", "HEAD", "config/").stdout.split()]
    for path in changed:
        m = SYMBOLS.match(path)
        if not m:
            continue
        gone = names("\n".join(diff_lines(REPO, decomp_tip, path, "-"))) - names(show(REPO, "HEAD", path))
        for region in regions:
            other = f"config/{region}/{m.group(2)}"
            if other != path:
                for name in sorted(gone & names(show(REPO, "HEAD", other))):
                    if m.group(1) == "jpn" and existing_regional_binding(
                            name, show(REPO, decomp_tip, path), show(REPO, "HEAD", path),
                            show(REPO, decomp_tip, other), show(REPO, "HEAD", other)):
                        continue
                    problems.append(f"HALF RENAME {name}: gone from {path}, still in {other}; rename it there too")
    return problems


def hooked_target():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return None
    command = str(event.get("tool_input", {}).get("command", ""))
    if not re.search(r"\bgh\s+pr\s+create\b", command):
        return None
    if "dqix-decomp-kit" in command:
        return "kit"
    if "dqix-decomp" in command:
        return "decomp"
    cwd = os.path.abspath(event.get("cwd") or os.getcwd()).replace("\\", "/").lower()
    return "decomp" if cwd.startswith(REPO.lower()) else "kit"


HOOK = sys.argv[1:] == ["--hook"]
if HOOK:
    target = hooked_target()
    if target is None:
        sys.exit(0)
elif sys.argv[1:] in (["kit"], ["decomp"]):
    target = sys.argv[1]
else:
    sys.exit(__doc__)
problems, kit_tip, decomp_tip = staleness()
problems += kit(kit_tip, decomp_tip) if target == "kit" else decomp(decomp_tip)
report = "\n".join(problems + [f"NOT READY: {len(problems)} problem(s)" if problems else "READY"])
if HOOK:
    if problems:
        print(f"prready.py {target}: fix these before opening the pull request.\n{report}", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
print(report)
sys.exit(1 if problems else 0)
