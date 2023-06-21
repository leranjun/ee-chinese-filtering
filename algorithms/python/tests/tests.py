"""
This module tests the AC module.
"""

import json
import logging
import unittest
from dataclasses import dataclass
from typing import cast

from chinese_filter import AC, WM, BruteForce, MatchResult, Native, Pattern, TargetText
from chinese_filter._common import BaseAlgo

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

CONFIG = {
    "BASE_PATH": "",
    "TEST_NAMES": ["1_short", "2_medium", "3_long"],
    # "TEST_NAMES": ["2_medium"],
}


@dataclass
class TestCase:
    """
    Dataclass for storing a test case.
    """

    blocklist: list[Pattern]
    testcase: TargetText
    expected: MatchResult


TESTS = {
    "0_en": TestCase(
        ["longlo", "ongword", "shortword", "shiningword", "longlongword"],
        "shortwordlonglongword",
        [(0, "shortword"), (9, "longlo"), (9, "longlongword"), (14, "ongword")],
    ),
    "0_zh": TestCase(["他", "她", "他的", "她的"], "他和她的", [(0, "他"), (2, "她"), (2, "她的")]),
}

with open(f"{CONFIG['BASE_PATH']}blocklist/blocklist_10.txt", encoding="utf-8") as file:
    blocklist = file.read().splitlines()

for test_name in CONFIG["TEST_NAMES"]:
    with open(f"{CONFIG['BASE_PATH']}tests/{test_name}.txt", encoding="utf-8") as file:
        test_case = file.read()
    with open(
        f"{CONFIG['BASE_PATH']}tests/res/{test_name}.json", encoding="utf-8"
    ) as file:
        test_res = cast(MatchResult, sorted([tuple(res) for res in json.load(file)]))
    TESTS[test_name] = TestCase(blocklist, test_case, test_res)


class TestAlgos(unittest.TestCase):
    """
    Test the algorithms.
    """

    def _run_test(
        self,
        algo: type[BaseAlgo],
    ) -> None:
        """
        Run a test case for a given instance of an algorithm and a given language.
        """
        for name, content in TESTS.items():
            if name != "0_zh" and name != "2_medium":
                continue
            instance = algo(content.blocklist)
            instance.dump()
            res = instance.match(content.testcase)
            self.assertEqual(sorted(res), content.expected, name)
            del instance

    def test_brute_force(self) -> None:
        """
        Test the brute force algorithm.
        """
        self._run_test(BruteForce)

    def test_native(self) -> None:
        """
        Test the native algorithm.
        """
        self._run_test(Native)

    def test_ac(self) -> None:
        """
        Test the AC algorithm.
        """
        self._run_test(AC)

    def test_wm(self) -> None:
        """
        Test the WM algorithm.
        """
        self._run_test(WM)


if __name__ == "__main__":
    CONFIG["BASE_PATH"] = "../../../"
    unittest.main()
