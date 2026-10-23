from copy import deepcopy
import json
import tempfile
import unittest
from pathlib import Path

from deku_installer.plan import MAX_ACTIONS, MAX_PLAN_BYTES, PlanValidationError, load_and_validate, validate_plan

EXAMPLE = Path(__file__).parents[1] / "examples" / "dry-run-plan.json"


class PlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_valid(self):
        self.assertEqual(validate_plan(self.plan), self.plan)

    def test_load_example(self):
        self.assertEqual(load_and_validate(EXAMPLE)["mode"], "plan-only")

    def test_unknown_schema_fails_closed(self):
        plan = deepcopy(self.plan)
        plan["schema_version"] = 99
        with self.assertRaisesRegex(PlanValidationError, "schema_version"):
            validate_plan(plan)

    def test_boolean_schema_version_is_rejected(self):
        plan = deepcopy(self.plan)
        plan["schema_version"] = True
        with self.assertRaisesRegex(PlanValidationError, "schema_version"):
            validate_plan(plan)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text(
                '{"schema_version":1,"schema_version":1}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PlanValidationError, "duplicate JSON object key"):
                load_and_validate(path)

    def test_oversized_plan_is_rejected_before_json_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "oversized.json"
            path.write_bytes(b" " * (MAX_PLAN_BYTES + 1))
            with self.assertRaisesRegex(PlanValidationError, "input limit"):
                load_and_validate(path)

    def test_invalid_utf8_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_bytes(b'{"invalid":"' + bytes([0xFF]) + b'"}')
            with self.assertRaisesRegex(PlanValidationError, "valid UTF-8 JSON"):
                load_and_validate(path)

    def test_excessive_json_nesting_is_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "deep.json"
            path.write_bytes(b"[" * 10_000 + b"0" + b"]" * 10_000)
            with self.assertRaisesRegex(PlanValidationError, "valid UTF-8 JSON"):
                load_and_validate(path)

    def test_action_count_is_bounded(self):
        plan = deepcopy(self.plan)
        plan["actions"] = [deepcopy(plan["actions"][0])] * (MAX_ACTIONS + 1)
        with self.assertRaisesRegex(PlanValidationError, "at most"):
            validate_plan(plan)

    def test_duplicate_boot_partition_actions_are_rejected(self):
        plan = deepcopy(self.plan)
        boot = {"type": "create_boot_partition", "size_mib": 256, "filesystem": "ext4"}
        plan["actions"].insert(-1, deepcopy(boot))
        plan["actions"].insert(-1, deepcopy(boot))
        with self.assertRaisesRegex(PlanValidationError, "at most one create_boot_partition"):
            validate_plan(plan)

    def test_missing_confirmation_gate_is_rejected(self):
        plan = deepcopy(self.plan)
        plan["confirmation"]["required"] = False
        with self.assertRaisesRegex(PlanValidationError, "required"):
            validate_plan(plan)

    def test_user_cannot_claim_destructive_confirmation_in_plan_only_mode(self):
        plan = deepcopy(self.plan)
        plan["confirmation"]["user_confirmed"] = True
        with self.assertRaisesRegex(PlanValidationError, "plan-only"):
            validate_plan(plan)

    def test_unknown_action_fails_closed(self):
        plan = deepcopy(self.plan)
        plan["actions"].insert(1, {"type": "run_shell", "command": "rm -rf /"})
        with self.assertRaisesRegex(PlanValidationError, "unsupported action"):
            validate_plan(plan)

    def test_layout_must_match_partition_table(self):
        plan = deepcopy(self.plan)
        plan["actions"][0]["table"] = "mbr"
        with self.assertRaisesRegex(PlanValidationError, "must be 'gpt'"):
            validate_plan(plan)

    def test_device_identifier_rejects_path_input(self):
        plan = deepcopy(self.plan)
        plan["target"]["device_id"] = "/dev/sda"
        with self.assertRaisesRegex(PlanValidationError, "device_id"):
            validate_plan(plan)

    def test_root_partition_must_be_last(self):
        plan = deepcopy(self.plan)
        plan["actions"][2], plan["actions"][1] = plan["actions"][1], plan["actions"][2]
        with self.assertRaises(PlanValidationError):
            validate_plan(plan)

    def test_unknown_top_level_field_is_rejected(self):
        plan = deepcopy(self.plan)
        plan["execute"] = True
        with self.assertRaisesRegex(PlanValidationError, "exactly"):
            validate_plan(plan)


if __name__ == "__main__":
    unittest.main()
