"""Bring the kit up to date: fetch the published kit and move this checkout onto it.

    python kit_update.py           at the start of every session and every time you stop
    python kit_update.py --hook    the same, as a Claude Code Stop hook (.claude/settings.json)
    python kit_update.py --dispatcher   from pull_all.sh once its slots have drained

Exit 0: up to date, or updated (then kit_init.py has run). 1: the fetch or kit_init.py failed; the
kit is unchanged or needs the FAIL lines fixed. 2: a fleet or an integration is running, so nothing
was pulled. 3: local changes, or unpublished commits that conflict with the update, block it.

Unpublished commits of your own (a recipe or a fix waiting in a kit pull request) are kept on top of
the update. Every changed agent instruction file is printed as `RE-READ <path>`: a running session
loaded the old one. With --hook the exit is always 0, and a JSON block decision asks the agent to
re-read those files before it stops. $DQIX_KIT_URL and $DQIX_KIT_BRANCH override the source
(default ZevyaDev/dqix-decomp-kit, main).
"""
import json
import os
import subprocess
import sys

import kitpaths

SP = kitpaths.SP
KIT = kitpaths.KIT
URL = kitpaths.KIT_URL
BRANCH = kitpaths.KIT_BRANCH
INSTRUCTIONS = ("AGENTS.md", "CLAUDE.md", ".claude/skills/", ".claude/workflows/", "worker_src/")
SLOW_TRIGGERS = ("colorsweep.py", "wdiff.py", "wgate.py", "regress.py", "regress_fixtures/")
HOOK = "--hook" in sys.argv
DISPATCHER = "--dispatcher" in sys.argv


def say(text):
    print(text, file=sys.stderr if HOOK else sys.stdout, flush=True)


def git(*args):
    return subprocess.run(["git", "-C", KIT, *args], capture_output=True, text=True)


def update():
    """-> (exit code, instruction files to re-read, kit_init ok)"""
    if git("fetch", "-q", URL, BRANCH).returncode != 0:
        say(f"FETCH FAILED {URL} {BRANCH}: continuing on the current version")
        return 1, [], True
    behind = int(git("rev-list", "--count", "HEAD..FETCH_HEAD").stdout.strip() or 0)
    if behind == 0:
        say("kit up to date")
        return 0, [], True
    busy = [b for b in kitpaths.busy() if not (DISPATCHER and b == "pull_all.pid")]
    if busy:
        say(f"UPDATE WAITING: {behind} commit(s); {', '.join(busy)} present. A running bash script "
            "must never be rewritten under it: stop the fleet (touch STOP_PULL FLEET_STOPPED, "
            "bash fullstop.sh), wait for the integration to finish, then rerun")
        return 2, [], True
    dirty = [l[3:] for l in git("status", "--porcelain", "--untracked-files=no").stdout.splitlines() if l.strip()]
    if dirty:
        say(f"UPDATE BLOCKED: {behind} commit(s) waiting; local changes to tracked files: {', '.join(dirty)}. "
            "Ask the user what to do with them; the kit takes only a recipe or a script fix as a pull request")
        return 3, [], True
    old = git("rev-parse", "HEAD").stdout.strip()
    local = int(git("rev-list", "--count", "FETCH_HEAD..HEAD").stdout.strip() or 0)
    if local == 0:
        moved = git("merge", "--ff-only", "-q", "FETCH_HEAD").returncode == 0
    else:
        moved = git("rebase", "-q", "FETCH_HEAD").returncode == 0
        if not moved:
            git("rebase", "--abort")
    if not moved:
        say(f"UPDATE BLOCKED: your {local} unpublished kit commit(s) conflict with the published kit; "
            f"resolve with git pull --rebase {URL} {BRANCH}")
        return 3, [], True
    new = git("rev-parse", "HEAD").stdout.strip()
    try:
        open(os.path.join(SP, "wlog", ".kit_fresh"), "w", encoding="utf-8").write("0")
    except OSError:
        pass
    changed = git("diff", "--name-only", old, new).stdout.split()
    say(f"updated {old[:8]}..{new[:8]}: {behind} commit(s), {len(changed)} file(s)"
        + (f"; your {local} unpublished commit(s) kept on top" if local else ""))
    reread = [f for f in changed if f.startswith(INSTRUCTIONS)]
    for f in reread:
        say(f"RE-READ {f}")
    argv = [sys.executable, "kit_init.py"]
    if any(f.startswith(SLOW_TRIGGERS) for f in changed):
        argv.append("--slow")
    ok = subprocess.run(argv, cwd=KIT, stdout=sys.stderr if HOOK else None).returncode == 0
    return (0 if ok else 1), reread, ok


code, reread, ok = update()
if not HOOK:
    sys.exit(code)
if reread or not ok:
    reason = "The kit was updated while you worked."
    if reread:
        reason += " Re-read before continuing: " + ", ".join(reread) + "."
    if not ok:
        reason += " kit_init.py failed after the update: run python kit_init.py and fix its FAIL lines."
    print(json.dumps({"decision": "block", "reason": reason}))
sys.exit(0)
