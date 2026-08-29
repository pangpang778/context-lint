"""argparse entrypoint + exit-code contract (0 clean / 1 violations / 2 internal).

Also the baseline-mode seam: --baseline-generate freezes current violations into a
snapshot file; --baseline compares the current run against one, marking pre-existing
findings [baseline] and excluding them from the exit-1 threshold.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from . import baseline
from .config_file import ConfigError
from .engine import run as run_engine

EXIT_CLEAN = 0
EXIT_VIOLATIONS = 1
EXIT_ERROR = 2


def _emit_errors(result):
    for err in result.errors:
        print(f"internal error on {err.file} [{err.rule}]: {err.message}", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="context_lint", description="Lint shipyard harness markdown discipline.")
    parser.add_argument("--root", default=".", help="repository root to scan (default: current directory)")
    parser.add_argument("--json", action="store_true", help="emit violations as a JSON object")
    baseline_group = parser.add_mutually_exclusive_group()
    baseline_group.add_argument("--baseline", metavar="FILE", help="compare against a version-1 baseline file")
    baseline_group.add_argument(
        "--baseline-generate",
        metavar="FILE",
        help="capture all current violations into a baseline file (exit 0)",
    )
    args = parser.parse_args(argv)

    try:
        result = run_engine(args.root)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    # --- generate mode: capture, exit 0 regardless of violations -----------------
    if args.baseline_generate:
        if result.errors:
            _emit_errors(result)
            return EXIT_ERROR
        records = [
            {"rule": it.violation.rule, "file": it.file, "message": it.violation.message} for it in result.items
        ]
        try:
            baseline.write_baseline(args.baseline_generate, records, datetime.now(timezone.utc).isoformat())
        except OSError as exc:
            print(f"baseline error: {exc}", file=sys.stderr)
            return EXIT_ERROR
        print(f"wrote baseline: {args.baseline_generate} ({len(records)} violations)")
        return EXIT_CLEAN

    # --- compare mode: classify matched (pre-existing) vs new -------------------
    baseline_counts = None
    if args.baseline:
        try:
            base_set = baseline.load_baseline(args.baseline)
        except baseline.BaselineError as exc:
            print(f"baseline error: {exc}", file=sys.stderr)
            _emit_errors(result)
            return EXIT_ERROR
        new_items, matched_items = baseline.filter_baseline(result.items, base_set)
        baseline_counts = {"matched": len(matched_items), "new": len(new_items)}
        violating_items = new_items  # only new findings drive exit 1
        matched_set = set(matched_items)
    else:
        violating_items = result.items
        matched_set = set()

    # exit 1 only when a surviving, non-exempt finding is severity "high" after override.
    exit_code = EXIT_ERROR if result.errors else (
        EXIT_VIOLATIONS if any(it.violation.severity == "high" for it in violating_items) else EXIT_CLEAN
    )

    if args.json:
        payload = {
            "findings": [it.violation.to_dict() for it in violating_items],
            "suppressed": result.suppressed,
        }
        if baseline_counts is not None:
            payload["baseline"] = baseline_counts
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        # order-preserving: render every finding, marking the matched (frozen) ones.
        for it in result.items:
            v = it.violation
            marker = " [baseline]" if it in matched_set else ""
            print(f"{it.file}:{v.line}: [{v.severity}] {v.rule}: {v.message}{marker}")

    _emit_errors(result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())