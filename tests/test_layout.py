from copy import deepcopy
import json
import unittest
from pathlib import Path

from deku_installer.layout import (
    MIB,
    MINIMUM_ROOT_BYTES,
    PARTITION_ALIGNMENT_BYTES,
    LayoutPreviewError,
    preview_layout,
)

EXAMPLE = Path(__file__).parents[1] / "examples" / "dry-run-plan.json"


class LayoutPreviewTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_produces_aligned_non_destructive_layout(self):
        layout = preview_layout(self.plan)
        self.assertEqual(layout.layout, "uefi-gpt")
        self.assertEqual([p.purpose for p in layout.partitions], ["efi", "root"])
        self.assertEqual(layout.partitions[0].size_bytes, 512 * MIB)
        self.assertGreaterEqual(layout.partitions[-1].size_bytes, MINIMUM_ROOT_BYTES)
        self.assertTrue(all(p.start_bytes % PARTITION_ALIGNMENT_BYTES == 0 for p in layout.partitions))
        self.assertFalse(layout.to_dict()["writes_performed"])

    def test_partition_ranges_are_ordered_and_non_overlapping(self):
        layout = preview_layout(self.plan)
        previous_end = layout.reserved_start_bytes
        for partition in layout.partitions:
            self.assertGreaterEqual(partition.start_bytes, previous_end)
            self.assertEqual(partition.end_bytes - partition.start_bytes, partition.size_bytes)
            previous_end = partition.end_bytes
        self.assertLessEqual(previous_end, layout.disk_size_bytes - MIB)

    def test_optional_boot_partition_is_after_efi_and_before_root(self):
        plan = deepcopy(self.plan)
        plan["actions"].insert(
            -1, {"type": "create_boot_partition", "size_mib": 1024, "filesystem": "ext4"}
        )
        layout = preview_layout(plan)
        self.assertEqual([p.purpose for p in layout.partitions], ["efi", "boot", "root"])
        self.assertEqual(layout.partitions[1].size_bytes, 1024 * MIB)
        self.assertLess(layout.partitions[0].end_bytes, layout.partitions[1].start_bytes)
        self.assertLess(layout.partitions[1].end_bytes, layout.partitions[2].start_bytes)

    def test_bios_mbr_layout_without_efi(self):
        plan = deepcopy(self.plan)
        plan["layout"] = "bios-mbr"
        plan["actions"] = [
            {"type": "create_partition_table", "table": "mbr"},
            {"type": "create_boot_partition", "size_mib": 512, "filesystem": "ext4"},
            {"type": "create_root_partition", "filesystem": "xfs", "remainder": True},
        ]
        layout = preview_layout(plan)
        self.assertEqual(layout.layout, "bios-mbr")
        self.assertEqual([p.purpose for p in layout.partitions], ["boot", "root"])
        self.assertEqual(layout.partitions[0].filesystem, "ext4")
        self.assertEqual(layout.partitions[1].filesystem, "xfs")

    def test_small_disk_is_rejected_by_preview(self):
        plan = deepcopy(self.plan)
        plan["target"]["size_bytes"] = 8704 * MIB
        with self.assertRaises(LayoutPreviewError):
            preview_layout(plan)

    def test_uefi_requires_efi_partition_first(self):
        plan = deepcopy(self.plan)
        plan["actions"] = [
            plan["actions"][0],
            plan["actions"][2],
            plan["actions"][1],
        ]
        with self.assertRaises(LayoutPreviewError):
            preview_layout(plan)

    def test_output_has_no_device_path_or_executable_actions(self):
        result = preview_layout(self.plan).to_dict()
        encoded = json.dumps(result)
        self.assertNotIn("/dev/", encoded)
        self.assertNotIn("mkfs", encoded)
        self.assertNotIn("parted", encoded)
        self.assertEqual(result["writes_performed"], False)

    def test_preview_is_deterministic(self):
        first = preview_layout(self.plan).to_dict()
        second = preview_layout(self.plan).to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
