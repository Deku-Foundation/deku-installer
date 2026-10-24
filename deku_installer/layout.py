"""Deterministic, non-destructive partition layout preview.

This module computes byte ranges only. It does not discover devices, call
partitioning tools, create filesystems, mount filesystems, or write disks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .plan import PlanValidationError, validate_plan

MIB = 1024 * 1024
PARTITION_ALIGNMENT_BYTES = MIB
RESERVED_START_BYTES = MIB
RESERVED_END_BYTES = MIB
MINIMUM_ROOT_BYTES = 8 * 1024 * MIB


class LayoutPreviewError(ValueError):
    """Raised when a valid plan cannot be translated into a safe preview."""


@dataclass(frozen=True)
class PartitionPreview:
    number: int
    purpose: str
    start_bytes: int
    end_bytes: int  # Exclusive end offset.
    size_bytes: int
    filesystem: str
    type_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayoutPreview:
    layout: str
    disk_size_bytes: int
    alignment_bytes: int
    reserved_start_bytes: int
    reserved_end_bytes: int
    unallocated_bytes: int
    partitions: tuple[PartitionPreview, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout": self.layout,
            "disk_size_bytes": self.disk_size_bytes,
            "alignment_bytes": self.alignment_bytes,
            "reserved_start_bytes": self.reserved_start_bytes,
            "reserved_end_bytes": self.reserved_end_bytes,
            "unallocated_bytes": self.unallocated_bytes,
            "partitions": [partition.to_dict() for partition in self.partitions],
            "writes_performed": False,
        }


def _align_up(value: int, alignment: int) -> int:
    return ((value + alignment - 1) // alignment) * alignment


def _align_down(value: int, alignment: int) -> int:
    return (value // alignment) * alignment


def preview_layout(plan: Any) -> LayoutPreview:
    """Return a deterministic partition preview for a validated plan.

    The preview reserves 1 MiB at both ends, aligns partitions to 1 MiB,
    places the EFI partition first on UEFI/GPT, and gives the remaining
    aligned extent to root. It deliberately does not output device paths or
    executable commands.
    """
    try:
        validate_plan(plan)
    except PlanValidationError:
        raise
    except (TypeError, KeyError, AttributeError) as exc:
        raise LayoutPreviewError(f"invalid plan structure: {exc}") from exc

    disk_size = plan["target"]["size_bytes"]
    layout = plan["layout"]
    actions = plan["actions"][1:]  # Partition-table declaration is not a partition.

    ordered_types = [action["type"] for action in actions]
    if not ordered_types or ordered_types[-1] != "create_root_partition":
        raise LayoutPreviewError("root partition must be the final partition action")

    if layout == "uefi-gpt":
        if ordered_types[0] != "create_efi_partition":
            raise LayoutPreviewError("UEFI/GPT layout requires the EFI partition first")
        if ordered_types.count("create_efi_partition") != 1:
            raise LayoutPreviewError("UEFI/GPT layout requires exactly one EFI partition")
        if "create_boot_partition" in ordered_types and ordered_types.index("create_boot_partition") != 1:
            raise LayoutPreviewError("optional /boot partition must follow the EFI partition")
    elif layout == "bios-mbr":
        if "create_efi_partition" in ordered_types:
            raise LayoutPreviewError("BIOS/MBR layout must not include an EFI partition")
        if "create_boot_partition" in ordered_types and ordered_types.index("create_boot_partition") != 0:
            raise LayoutPreviewError("optional /boot partition must precede root")

    limit = _align_down(disk_size - RESERVED_END_BYTES, PARTITION_ALIGNMENT_BYTES)
    if limit <= RESERVED_START_BYTES:
        raise LayoutPreviewError("target disk is too small for the reserved layout boundaries")

    cursor = _align_up(RESERVED_START_BYTES, PARTITION_ALIGNMENT_BYTES)
    partitions: list[PartitionPreview] = []
    root_action: dict[str, Any] | None = None

    for action in actions:
        action_type = action["type"]
        if action_type == "create_root_partition":
            root_action = action
            break

        size_bytes = action["size_mib"] * MIB
        start = _align_up(cursor, PARTITION_ALIGNMENT_BYTES)
        end = start + size_bytes
        if end > limit:
            raise LayoutPreviewError(
                f"disk is too small for {action_type} plus the reserved end boundary"
            )

        if action_type == "create_efi_partition":
            purpose, filesystem, type_hint = "efi", "vfat", "efi-system"
        elif action_type == "create_boot_partition":
            purpose, filesystem, type_hint = "boot", action["filesystem"], "linux-filesystem"
        else:
            raise LayoutPreviewError(f"unsupported partition action: {action_type}")

        partitions.append(
            PartitionPreview(
                number=len(partitions) + 1,
                purpose=purpose,
                start_bytes=start,
                end_bytes=end,
                size_bytes=size_bytes,
                filesystem=filesystem,
                type_hint=type_hint,
            )
        )
        cursor = end

    if root_action is None:
        raise LayoutPreviewError("root partition action is missing")

    root_start = _align_up(cursor, PARTITION_ALIGNMENT_BYTES)
    root_end = limit
    root_size = root_end - root_start
    if root_size < MINIMUM_ROOT_BYTES:
        raise LayoutPreviewError(
            "target disk cannot provide the minimum 8 GiB root filesystem after alignment and reserved space"
        )

    partitions.append(
        PartitionPreview(
            number=len(partitions) + 1,
            purpose="root",
            start_bytes=root_start,
            end_bytes=root_end,
            size_bytes=root_size,
            filesystem=root_action["filesystem"],
            type_hint="linux-filesystem",
        )
    )

    previous_end = RESERVED_START_BYTES
    for partition in partitions:
        if partition.start_bytes % PARTITION_ALIGNMENT_BYTES != 0:
            raise LayoutPreviewError("internal layout error: partition start is not aligned")
        if partition.start_bytes < previous_end:
            raise LayoutPreviewError("internal layout error: partition ranges overlap")
        if partition.end_bytes <= partition.start_bytes:
            raise LayoutPreviewError("internal layout error: partition has a non-positive size")
        previous_end = partition.end_bytes

    allocated = sum(partition.size_bytes for partition in partitions)
    return LayoutPreview(
        layout=layout,
        disk_size_bytes=disk_size,
        alignment_bytes=PARTITION_ALIGNMENT_BYTES,
        reserved_start_bytes=RESERVED_START_BYTES,
        reserved_end_bytes=disk_size - root_end,
        unallocated_bytes=disk_size - allocated,
        partitions=tuple(partitions),
    )
