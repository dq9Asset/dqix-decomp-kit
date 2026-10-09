#!/usr/bin/env python3
"""Coverage, from the build's own report -- the same number every wave prints.

    python cov.py            ->  (11637/14778) 78.75%
    python cov.py --config   ->  config-derived estimate, when no build report exists
    python cov.py --details  ->  report-only function and code-byte measures (no estimate)

`build/usa/report.json` is the authoritative measure: `finish_wave` reads exactly these fields, so
every historical figure in this project (46.43%, 78.64%, ...) is on this scale.

DO NOT SUBSTITUTE A DIFFERENT METRIC. The first version of this file counted function symbols
falling inside delink ranges instead, and read 11654/14733 = 79.10% against the wave's
11637/14778 = 78.75%. Both are defensible; they are not the same question, and quietly swapping
one for the other makes progress look like it jumped 0.35 points when nothing changed. The config
estimate is kept only as a labelled fallback for when no build has run yet.
"""
import os as _kpos, sys as _kpsys
_kpsys.path.insert(0, _kpos.path.dirname(_kpos.path.abspath(__file__)))
import kitpaths as _kp
import json
import os
import re
import sys

REPO = _kp.REPO
REGION = os.environ.get("DQIX_REGION", "usa")
REPORT = f"{REPO}/build/{REGION}/report.json"
CFG = f"{REPO}/config/{REGION}/arm9"

FUNC = re.compile(r"(?m)^(\S+)\s+kind:function\((?:arm|thumb),size=0x([0-9a-fA-F]+)\)"
                  r"\s+addr:0x([0-9a-fA-F]+)")
RANGE = re.compile(r"(?m)^\s*\.(?:text|init) start:0x([0-9a-fA-F]+) end:0x([0-9a-fA-F]+)\s*$")


def from_report():
    m = json.load(open(REPORT, encoding="utf-8"))["measures"]
    return m["matched_functions"], m["total_functions"], m["matched_functions_percent"]


def report_details():
    """Return distinct authoritative measures; never infer byte coverage from functions."""
    m = json.load(open(REPORT, encoding="utf-8"))["measures"]
    lines = [f"{REGION.upper()} objdiff report: {REPORT}"]
    for label, matched_key, total_key in (
            ("functions", "matched_functions", "total_functions"),
            ("code bytes", "matched_code", "total_code")):
        matched, total = int(m[matched_key]), int(m[total_key])
        if matched < 0 or total < 0 or matched > total:
            raise ValueError(f"invalid {label} counts")
        percent = f"{100.0 * matched / total:.2f}%" if total else "n/a"
        lines.append(f"{label}: {matched}/{total} ({percent})")
    return "\n".join(lines)


def from_config():
    """Fallback only. Counts function symbols inside delink ranges across every module."""
    mods = [CFG]
    ovdir = f"{CFG}/overlays"
    if os.path.isdir(ovdir):
        mods += [f"{ovdir}/{d}" for d in sorted(os.listdir(ovdir))]
    matched = total = 0
    for cfg in mods:
        try:
            sym = open(f"{cfg}/symbols.txt", encoding="utf-8", errors="ignore").read()
            dl = open(f"{cfg}/delinks.txt", encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        done = [(int(a, 16), int(b, 16)) for a, b in RANGE.findall(dl)]
        for _n, size, addr in FUNC.findall(sym):
            if not int(size, 16):
                continue
            total += 1
            a = int(addr, 16)
            if any(s <= a < e for s, e in done):
                matched += 1
    return matched, total, (100.0 * matched / total if total else 0.0)


def main():
    if "--details" in sys.argv:
        if "--config" in sys.argv:
            print("--details requires the objdiff report; --config is an estimate", file=sys.stderr)
            return 1
        try:
            print(report_details())
        except (OSError, KeyError, TypeError, ValueError) as exc:
            print(f"{REGION.upper()} authoritative report unavailable: {exc}", file=sys.stderr)
            return 1
        return 0
    want_config = "--config" in sys.argv
    if not want_config and os.path.exists(REPORT):
        m, t, pct = from_report()
        print(f"({m}/{t}) {pct:.2f}%")
        return 0
    m, t, pct = from_config()
    # Say so. An estimate presented as the real figure is how two scales get mixed up.
    print(f"({m}/{t}) {pct:.2f}% [config estimate, no build report]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
