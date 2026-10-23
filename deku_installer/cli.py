"""Command-line entry point for non-destructive plan validation."""
from __future__ import annotations

import argparse
import sys

from .plan import PlanValidationError, load_and_validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Deku Installer plan without modifying the system")
    parser.add_argument("plan", help="path to a JSON plan file")
    args = parser.parse_args()
    try:
        plan = load_and_validate(args.plan)
    except PlanValidationError as exc:
        print(f"invalid plan: {exc}", file=sys.stderr)
        return 2
    print("plan valid (plan-only; no system changes performed)")
    print(f"target: {plan['target']['device_id']} ({plan['target']['model']})")
    print(f"layout: {plan['layout']}; actions: {len(plan['actions'])}")
    print("destructive confirmation remains required; execution is not implemented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
