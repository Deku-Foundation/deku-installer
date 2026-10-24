"""Command-line entry point for non-destructive plan validation and layout preview."""
from __future__ import annotations

import argparse
import sys

from .layout import LayoutPreviewError, preview_layout
from .plan import PlanValidationError, load_and_validate


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Deku Installer plan and show a non-destructive partition preview"
    )
    parser.add_argument("plan", help="path to a JSON plan file")
    args = parser.parse_args()
    try:
        plan = load_and_validate(args.plan)
        layout = preview_layout(plan)
    except (PlanValidationError, LayoutPreviewError, ValueError) as exc:
        print(f"invalid plan/layout: {exc}", file=sys.stderr)
        return 2

    print("plan valid (plan-only; no system changes performed)")
    print(f"target fixture: {plan['target']['device_id']} ({plan['target']['model']})")
    print(f"layout: {layout.layout}; disk size: {layout.disk_size_bytes} bytes")
    print(f"alignment: {layout.alignment_bytes} bytes; partitions: {len(layout.partitions)}")
    for partition in layout.partitions:
        print(
            f"  {partition.number}. {partition.purpose}: "
            f"start={partition.start_bytes} end_exclusive={partition.end_bytes} "
            f"size={partition.size_bytes} fs={partition.filesystem} "
            f"type_hint={partition.type_hint}"
        )
    print(
        f"unallocated bytes: {layout.unallocated_bytes}; "
        "writes_performed=false"
    )
    print("destructive confirmation remains required; execution is not implemented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
