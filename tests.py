"""This module tests the AC module."""

import json
import logging
import unittest
from typing import cast

from benchmark import (
    BASE_PATH,
    BLOCKLIST_NAMES,
    TEST_NAMES,
    Blocklist,
    BlocklistName,
    TestCase,
    validate_test_case,
)
from src import (
    AC,
    ENHANCEMENTS,
    WM,
    BaseAlgo,
    BruteForce,
    EnhancementType,
    MatchResult,
    Native,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class TestAlgos(unittest.TestCase):
    """Test the algorithms."""

    maxDiff = None
    blocklists: list[Blocklist] = []
    tests: dict[BlocklistName, list[TestCase]] = {}

    def setUp(self) -> None:
        """Set up the test case."""
        blocklist_dir = BASE_PATH / "blocklist"
        if not blocklist_dir.exists():
            raise FileNotFoundError("Blocklist directory does not exist")

        test_dir = BASE_PATH / "tests"
        if not test_dir.exists():
            raise FileNotFoundError("Test directory does not exist")

        test_res_dir = BASE_PATH / "tests" / "res"
        if not test_res_dir.exists():
            raise FileNotFoundError("Test result directory does not exist")

        for blocklist_name in BLOCKLIST_NAMES:
            with open(
                blocklist_dir / f"blocklist_{blocklist_name}.txt",
                encoding="utf-8",
            ) as file:
                self.blocklists.append(
                    Blocklist(blocklist_name, file.read().splitlines())
                )

            for test_name in TEST_NAMES:
                with open(test_dir / f"{test_name}.txt", encoding="utf-8") as file:
                    testcase = file.read()

                expected: dict[EnhancementType, list[MatchResult]] = {}
                for enhancement in ENHANCEMENTS:
                    if not validate_test_case(enhancement, blocklist_name):
                        continue

                    with open(
                        test_res_dir
                        / blocklist_name
                        / enhancement
                        / f"{test_name}.json",
                        encoding="utf-8",
                    ) as file:
                        cur_res = cast(
                            list[MatchResult],
                            [
                                [tuple(match) for match in res]
                                for res in json.load(file)
                            ],
                        )

                    expected[enhancement] = cur_res

                self.tests.setdefault(blocklist_name, []).append(
                    TestCase(test_name, testcase, expected)
                )

        logging.debug("Blocklists: %d", len(self.blocklists))
        logging.debug("Tests: %d", len(self.tests))

    def _run_test(
        self,
        algo: type[BaseAlgo],
    ) -> None:
        """Run a test case for a given instance of an algorithm and a given language."""
        for blocklist in self.blocklists:
            for enhancement in ENHANCEMENTS:
                logging.info(
                    "Testing %s - %s - %s",
                    algo.__name__,
                    blocklist.name,
                    enhancement,
                )
                enable_radical = "radical" in enhancement
                enable_pinyin = "pinyin" in enhancement
                if not validate_test_case(enhancement, blocklist.name):
                    continue

                instance = algo(
                    blocklist.patterns,
                    enable_radical=enable_radical,
                    enable_pinyin=enable_pinyin,
                )
                logging.info(
                    "Created %s instance (enable_radical=%s, enable_pinyin=%s)",
                    algo.__name__,
                    enable_radical,
                    enable_pinyin,
                )

                for test in self.tests[blocklist.name]:
                    logging.info("Testing %s", test.name)
                    res = instance.match(test.testcase)
                    res = sorted([sorted(r) for r in res])
                    self.assertEqual(
                        res,
                        test.expected[enhancement],
                        (
                            f"Results do not match for {test.name}\n"
                            f"Expected: {test.expected[enhancement]}\n"
                            f"Got: {res}\n"
                            f"Radical map: {hasattr(instance, 'radical_map')}\n"
                            f"Pinyin map: {hasattr(instance, 'pinyin_map')}"
                        ),
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
