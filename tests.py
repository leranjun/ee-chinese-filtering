"""This module tests the AC module."""

import json
import logging
import unittest
from dataclasses import dataclass
from typing import Literal, cast, get_args

from src import AC, WM, BaseAlgo, BruteForce, MatchResult, Native, Pattern, TargetText

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

Enhancements = Literal["naive", "pinyin", "radical", "radical_pinyin"]


@dataclass
class TestCase:
    """Dataclass for storing a test case."""

    blocklist: list[Pattern]
    testcase: TargetText
    expected: dict[Enhancements, list[MatchResult]]


class TestAlgos(unittest.TestCase):
    """Test the algorithms."""

    maxDiff = None
    ENHANCEMENTS = get_args(Enhancements)
    CONFIG = {
        "BASE_PATH": "./",
        "TEST_NAMES": ["1_short", "2_medium", "3_long"],
        # "TEST_NAMES": ["2_medium"],
    }

    def setUp(self) -> None:
        """Set up the test case."""
        self.tests = {
            "0_en": TestCase(
                ["longlo", "ongword", "shortword", "shiningword", "longlongword"],
                "shortwordlonglongword",
                {
                    k: [
                        [
                            (0, "shortword"),
                            (9, "longlo"),
                            (9, "longlongword"),
                            (14, "ongword"),
                        ]
                    ]
                    for k in self.ENHANCEMENTS
                },
            ),
            "0_zh": TestCase(
                ["他", "她", "他的", "她的"],
                "他和她的",
                {k: [[(0, "他"), (2, "她"), (2, "她的")]] for k in self.ENHANCEMENTS},
            ),
        }

        with open(
            f"{self.CONFIG['BASE_PATH']}blocklist/blocklist_10.txt", encoding="utf-8"
        ) as file:
            blocklist = file.read().splitlines()

        for test_name in self.CONFIG["TEST_NAMES"]:
            with open(
                f"{self.CONFIG['BASE_PATH']}tests/{test_name}.txt", encoding="utf-8"
            ) as file:
                test_case = file.read()

            test_res: dict[Enhancements, list[MatchResult]] = {}
            for enhancement in self.ENHANCEMENTS:
                with open(
                    f"{self.CONFIG['BASE_PATH']}tests/res/{enhancement}/{test_name}.json",
                    encoding="utf-8",
                ) as file:
                    cur_res = cast(
                        list[MatchResult],
                        sorted(
                            [
                                sorted([tuple(match) for match in res])
                                for res in json.load(file)
                            ]
                        ),
                    )

                test_res[enhancement] = cur_res

            self.tests[test_name] = TestCase(blocklist, test_case, test_res)

    def _run_test(
        self,
        algo: type[BaseAlgo],
    ) -> None:
        """Run a test case for a given instance of an algorithm and a given language."""
        for name, content in self.tests.items():
            for enhancement in self.ENHANCEMENTS:
                enable_radical = "radical" in enhancement
                enable_pinyin = "pinyin" in enhancement
                logging.debug(
                    "Test %s with %s enhancement, enable_radical=%s, enable_pinyin=%s",
                    name,
                    enhancement,
                    enable_radical,
                    enable_pinyin,
                )
                instance = algo(content.blocklist, enable_radical, enable_pinyin)
                instance.dump()
                res = instance.match(content.testcase)
                self.assertEqual(
                    sorted([sorted(r) for r in res]),
                    sorted(content.expected[enhancement]),
                    name,
                )

    def test_brute_force(self) -> None:
        """Test the brute force algorithm."""
        self._run_test(BruteForce)

    def test_native(self) -> None:
        """Test the native algorithm."""
        self._run_test(Native)

    def test_ac(self) -> None:
        """Test the AC algorithm."""
        self._run_test(AC)

    def test_wm(self) -> None:
        """Test the WM algorithm."""
        self._run_test(WM)


if __name__ == "__main__":
    unittest.main()
