import json
import unittest
from copy import deepcopy
from pathlib import Path

from deku_installer.plan import PlanValidationError, validate_plan

EXAMPLE = Path(__file__).parents[1] / "examples" / "dry-run-plan.json"


class TargetCapacityTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_rejects_disk_smaller_than_layout_minimum(self):
        plan = deepcopy(self.plan)
        plan["target"]["size_bytes"] = 1024 * 1024
        with self.assertRaisesRegex(PlanValidationError, "too small"):
            validate_plan(plan)

    def test_accepts_example_capacity(self):
        self.assertEqual(validate_plan(self.plan), self.plan)


if __name__ == "__main__":
    unittest.main()
