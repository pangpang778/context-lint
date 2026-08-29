"""argparse entrypoint + exit-code contract (0 clean / 1 violations / 2 internal)."""

import argparse
import json
import sys

from .engine import run as run_engine

EXIT_CLEAN = 0
EXIT_VIOLATIONS = 1
EXIT_ERROR = 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="context_lint", description="Lint shipyard harness markdown discipline.")
    parser.add_argument("--root", default=".", help="repository root to scan (default: current directory)")
    parser.add_argument("--json", action="store_true", help="emit violations as a JSON list")
    args = parser.parse_args(argv)

    result = run_engine(args.root)
    exit_code = EXIT_ERROR if result.errors else (EXIT_VIOLATIONS if result.items else EXIT_CLEAN)

    if args.json:
        payload = {
            "findings": [it.violation.to_dict() for it in result.items],
            "suppressed": result.suppressed,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for it in result.items:
            v = it.violation
            print(f"{it.file}:{v.line}: [{v.severity}] {v.rule}: {v.message}")
    # errors always surface on stderr, even under --json (never silently swallow)
    for err in result.errors:
        print(f"internal error on {err.file} [{err.rule}]: {err.message}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())