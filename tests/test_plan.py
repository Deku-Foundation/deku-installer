from copy import deepcopy
import json
import unittest
from pathlib import Path

from deku_installer.plan import PlanValidationError, load_and_validate, validate_plan

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
