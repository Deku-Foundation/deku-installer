"""Validate Deku installer plans without touching system devices."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SUPPORTED_LAYOUTS = {"uefi-gpt", "bios-mbr"}
SUPPORTED_ACTIONS = {
    "create_partition_table",
    "create_efi_partition",
    "create_boot_partition",
    "create_root_partition",
}
_DEVICE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class PlanValidationError(ValueError):
    """Raised when a plan is malformed or requests unsupported behavior."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanValidationError(message)


def validate_plan(plan: Any) -> dict[str, Any]:
    """Validate a plan-only JSON object and return it unchanged.

    This function is intentionally pure: it performs no device discovery,
    privilege escalation, downloads, mounts, or disk writes.
    """
    _require(isinstance(plan, dict), "plan must be a JSON object")
    allowed_top = {"schema_version", "mode", "target", "layout", "actions", "confirmation"}
    _require(set(plan) == allowed_top, "plan must contain exactly the documented top-level fields")
    _require(plan["schema_version"] == SCHEMA_VERSION, "unsupported schema_version")
    _require(plan["mode"] == "plan-only", "only mode 'plan-only' is supported by this prototype")
    _require(isinstance(plan["layout"], str) and plan["layout"] in SUPPORTED_LAYOUTS, "unsupported partition layout")

    target = plan["target"]
    _require(isinstance(target, dict), "target must be an object")
    _require(set(target) == {"device_id", "size_bytes", "model"}, "target must contain device_id, size_bytes, and model only")
    _require(isinstance(target["device_id"], str) and bool(_DEVICE_ID.fullmatch(target["device_id"])), "target.device_id has invalid format")
    _require(isinstance(target["size_bytes"], int) and not isinstance(target["size_bytes"], bool) and target["size_bytes"] > 0, "target.size_bytes must be a positive integer")
    _require(isinstance(target["model"], str) and 1 <= len(target["model"].strip()) <= 200, "target.model must be a non-empty string of at most 200 characters")

    actions = plan["actions"]
    _require(isinstance(actions, list) and actions, "actions must be a non-empty array")
    for index, action in enumerate(actions):
        prefix = f"actions[{index}]"
        _require(isinstance(action, dict), f"{prefix} must be an object")
        action_type = action.get("type")
        _require(isinstance(action_type, str) and action_type in SUPPORTED_ACTIONS, f"{prefix} has an unsupported action type")
        if action_type == "create_partition_table":
            _require(set(action) == {"type", "table"}, f"{prefix} has invalid fields")
            expected = "gpt" if plan["layout"] == "uefi-gpt" else "mbr"
            _require(action["table"] == expected, f"{prefix}.table must be {expected!r} for the selected layout")
        elif action_type == "create_efi_partition":
            _require(set(action) == {"type", "size_mib"}, f"{prefix} has invalid fields")
            _require(plan["layout"] == "uefi-gpt", f"{prefix} is only valid for uefi-gpt")
            _require(isinstance(action["size_mib"], int) and not isinstance(action["size_mib"], bool) and 100 <= action["size_mib"] <= 4096, f"{prefix}.size_mib must be between 100 and 4096")
        elif action_type == "create_boot_partition":
            _require(set(action) == {"type", "size_mib", "filesystem"}, f"{prefix} has invalid fields")
            _require(isinstance(action["size_mib"], int) and not isinstance(action["size_mib"], bool) and 128 <= action["size_mib"] <= 4096, f"{prefix}.size_mib must be between 128 and 4096")
            _require(isinstance(action["filesystem"], str) and action["filesystem"] in {"ext4", "xfs"}, f"{prefix}.filesystem is unsupported")
        elif action_type == "create_root_partition":
            _require(set(action) == {"type", "filesystem", "remainder"}, f"{prefix} has invalid fields")
            _require(isinstance(action["filesystem"], str) and action["filesystem"] in {"ext4", "xfs", "btrfs"}, f"{prefix}.filesystem is unsupported")
            _require(action["remainder"] is True, f"{prefix}.remainder must be true in schema v1")

    # Schema v1 reserves at least 8 GiB for the root filesystem in the plan.
    # This is only a conservative planning check, not a partitioning implementation.
    reserved_mib = 8192
    reserved_mib += sum(
        action.get("size_mib", 0)
        for action in actions
        if action.get("type") in {"create_efi_partition", "create_boot_partition"}
        and isinstance(action.get("size_mib", 0), int)
        and not isinstance(action.get("size_mib", 0), bool)
    )
    _require(target["size_bytes"] >= reserved_mib * 1024 * 1024, "target disk is too small for the requested layout and minimum root space")

    confirmation = plan["confirmation"]
    _require(isinstance(confirmation, dict), "confirmation must be an object")
    _require(set(confirmation) == {"required", "user_confirmed"}, "confirmation must contain required and user_confirmed only")
    _require(confirmation["required"] is True, "confirmation.required must always be true")
    _require(confirmation["user_confirmed"] is False, "plan-only validation must not represent destructive confirmation")

    action_types = [item["type"] for item in actions]
    _require(action_types.count("create_partition_table") == 1, "exactly one create_partition_table action is required")
    _require(action_types.count("create_root_partition") == 1, "exactly one create_root_partition action is required")
    if plan["layout"] == "uefi-gpt":
        _require(action_types.count("create_efi_partition") == 1, "uefi-gpt plans require exactly one EFI partition action")
    else:
        _require("create_efi_partition" not in action_types, "bios-mbr plans must not include an EFI partition")
    _require(action_types.index("create_partition_table") == 0, "partition table action must be first")
    _require(action_types.index("create_root_partition") == len(actions) - 1, "root partition action must be last")
    return plan


def load_and_validate(path: str | Path) -> dict[str, Any]:
    """Load a UTF-8 JSON plan and validate it."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            plan = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanValidationError(f"cannot read valid JSON plan: {exc}") from exc
    return validate_plan(plan)
