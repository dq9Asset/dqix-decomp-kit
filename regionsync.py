"""Port matched files from config/usa to every other region, keeping each port only if that region builds.

    python regionsync.py [decomp tree]     default: the current directory

For each region with a port tool that has --sync and an extracted ROM: run the sync (after building the
region first when its tool reads that region's objects), build the region, commit the ported config
when `ninja check` and `ninja sha1` pass. When they do not, restore the config of each module whose
check failed and build again; restore the whole region when that is still red or no module is named.
The tree is reconfigured for usa afterwards. Exit 0: every region in sync, ported or skipped. 1: a port
was red and was restored, in part or in full.
"""
import os
import re
import subprocess
import sys
import time

import kitpaths

PORTS = {"eur": "tools/port_eur_config.py", "jpn": "tools/port_jpn_config.py"}
READS_OBJECTS = {"jpn"}
FAILED_CHECK = re.compile(r"Check (ARM9 main|ITCM|DTCM|overlay (\d+)): (?!OK)")
PORTED_FILE = re.compile(r"^\+[^+\s].*:\r?$", re.M)


def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def configure(region):
    compiler = os.environ.get("DQIX_PREINSTALLED_COMPILER")
    return run(sys.executable, "tools/configure.py", region, "--no-extract", *(["--compiler", compiler] if compiler else []))


def green():
    code, out = run("ninja", "check")
    if code:
        return False, out
    code, sha = run("ninja", "sha1")
    return code == 0 and "OK" in sha, out + sha


def ported(region):
    return len(PORTED_FILE.findall(run("git", "diff", "-U0", "--", f"config/{region}")[1]))


def failed_modules(log, region):
    root = f"config/{region}/arm9"
    folders = {root if m[1] == "ARM9 main" else f"{root}/overlays/ov{int(m[2]):03d}" if m[2] else f"{root}/{m[1].lower()}"
               for m in FAILED_CHECK.finditer(log)}
    changed = run("git", "diff", "--name-only", "--", root)[1].split()
    return [path for path in changed if os.path.dirname(path) in folders]


def sync(region, tool):
    if not os.path.isfile(tool) or "--sync" not in run(sys.executable, tool, "--help")[1]:
        return 0, f"{region}: {tool} has no --sync, not ported"
    if not os.path.isdir(f"extract/{region}"):
        return 0, f"{region}: no extracted {region} ROM, not ported"
    if region in READS_OBJECTS:
        configure(region)
        run("ninja", "-k", "0", "check")
    code, out = run(sys.executable, tool, "--sync")
    if code:
        run("git", "checkout", "--", f"config/{region}")
        return 1, f"{region}: {tool} --sync failed: {out.strip().splitlines()[-1:]}"
    if not run("git", "status", "--porcelain", "--", f"config/{region}")[1].strip():
        return 0, f"{region}: in sync"
    files = ported(region)
    configure(region)
    ok, log = green()
    dropped = [] if ok else failed_modules(log, region)
    if dropped:
        run("git", "checkout", "--", *dropped)
        configure(region)
        ok, retry = green()
        ok = ok and bool(run("git", "status", "--porcelain", "--", f"config/{region}")[1].strip())
        log += retry
    if dropped or not ok:
        path = f"{kitpaths.SP}/wlog/regionsync_{region}_{time.strftime('%m%d_%H%M')}.log"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out + log)
    if not ok:
        run("git", "checkout", "--", f"config/{region}")
        return 1, f"{region}: RED after porting {files} files, restored; log {path}"
    files = ported(region)
    run("git", "add", "--", f"config/{region}")
    message = f"Port {files} matched files to {region.upper()}" if files else f"Port USA names to {region.upper()}"
    code, out = run("git", "commit", "-q", "-m", message)
    if code:
        run("git", "reset", "-q", "--", f"config/{region}")
        run("git", "checkout", "--", f"config/{region}")
        return 1, f"{region}: commit failed, restored: {out.strip()[-200:]}"
    if dropped:
        return 1, f"{region}: {message}; restored red {', '.join(sorted({os.path.dirname(p) for p in dropped}))}; log {path}"
    return 0, f"{region}: {message}"


def main():
    if len(sys.argv) > 2 or sys.argv[1:2] in (["-h"], ["--help"]):
        sys.exit(__doc__)
    if len(sys.argv) == 2:
        os.chdir(sys.argv[1])
    status = 0
    try:
        for region, tool in PORTS.items():
            code, line = sync(region, tool)
            status |= code
            print(line)
    finally:
        configure("usa")
    sys.exit(status)


if __name__ == "__main__":
    main()
