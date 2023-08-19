"""Benchmarking script for the algorithms."""

import csv
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, cast, get_args

from src import (
    ALGOS,
    ENHANCEMENTS,
    AlgoName,
    AlgoType,
    EnhancementType,
    MatchResult,
    Pattern,
    TargetText,
)
from src.profile import profile

BASE_PATH = Path("./")
TestName = Literal["1_short", "2_medium", "3_long"]
BlocklistName = Literal["10", "100", "1k", "10k", "full", "wm"]
TEST_NAMES = cast(tuple[TestName, ...], get_args(TestName))
BLOCKLIST_NAMES = cast(tuple[BlocklistName, ...], get_args(BlocklistName))


Time = float
Mem = float


@dataclass
class Blocklist:
    """Dataclass for storing a blocklist."""

    name: BlocklistName
    patterns: list[Pattern]


@dataclass
class TestCase:
    """Dataclass for storing a test case."""

    name: TestName
    testcase: TargetText
    expected: dict[EnhancementType, list[MatchResult]]


# Results
@dataclass
class TestResult:
    """Dataclass for storing the results of a test."""

    case_name: TestName
    time: Time
    mem: Mem


@dataclass
class RunResult:
    """Dataclass for storing the results of a test."""

    enhancement: EnhancementType
    creation_time: Time
    creation_mem: Mem
    test_results: list[TestResult]


@dataclass
class AlgoResult:
    """Dataclass for storing the results of a test."""

    algo: AlgoName
    blocklist_name: BlocklistName
    run_results: list[RunResult]

    def __str__(self) -> str:
        return (
            "========================================\n"
            + f"Algorithm: {self.algo}\n"
            + f"Blocklist size: {self.blocklist_name}\n"
            + "\n".join(
                "----------------------------------------\n"
                f"Enhancement: {res.enhancement}\n"
                + f"Creation time: {res.creation_time}\n"
                + f"Creation memory: {res.creation_mem}\n"
                + "\n"
                + "\n".join(
                    f"Test case: {test_res.case_name}\n"
                    + f"Time: {test_res.time}\n"
                    + f"Memory: {test_res.mem}\n"
                    for test_res in res.test_results
                )
                + "----------------------------------------\n"
                for res in self.run_results
            )
            + "========================================\n"
        )

    def to_csv_dicts(self) -> list[dict[str, str]]:
        """Convert the results to a list of dictionaries for CSV export."""
        res: list[dict[str, str]] = []

        for run_result in self.run_results:
            cur_res: dict[str, str] = {
                "algo": self.algo,
                "blocklist_name": self.blocklist_name,
                "enhancement": run_result.enhancement,
                "creation_time": str(run_result.creation_time),
                "creation_mem": str(run_result.creation_mem),
            }

            for test_result in run_result.test_results:
                cur_res[f"test_{test_result.case_name}_time"] = str(test_result.time)
                cur_res[f"test_{test_result.case_name}_mem"] = str(test_result.mem)

            res.append(cur_res)

        return res


def validate_test_case(
    enhancement: EnhancementType, blocklist_name: BlocklistName
) -> bool:
    """Validate whether a test case is runnable."""
    pinyin_skip: tuple[BlocklistName, ...] = ("1k", "10k", "full", "wm")
    radical_skip: tuple[BlocklistName, ...] = ("full",)
    if ("pinyin" in enhancement and blocklist_name in pinyin_skip) or (
        "radical" in enhancement and blocklist_name in radical_skip
    ):
        logging.info("Skipping %s - %s", blocklist_name, enhancement)
        return False

    return True


@profile(backend="psutil_uss")
def create_instance(
    algo: type[AlgoType],
    blocklist_content: list[Pattern],
    enable_radical: bool = False,
    enable_pinyin: bool = False,
) -> tuple[
    Annotated[AlgoType, "Created instance"],
    Annotated[Time, "Time taken to crete instance"],
]:
    """Create an instance of a given algorithm."""
    time_start = time.time()
    instance = algo(blocklist_content, enable_radical, enable_pinyin)
    time_end = time.time()
    return instance, time_end - time_start


@profile(backend="psutil_uss")
def match_with_instance(
    instance: AlgoType, text: TargetText
) -> tuple[
    Annotated[list[MatchResult], "Match results"],
    Annotated[Time, "Time taken to match"],
]:
    """Match a given test case with a given instance of an algorithm."""
    time_start = time.time()
    res = instance.match(text)
    time_end = time.time()
    return res, time_end - time_start


def test_algo(
    algo: type[AlgoType],
    blocklist: Blocklist,
    tests: list[TestCase],
) -> AlgoResult:
    """Test a given algorithm with a given blocklist and tests."""
    logging.info(
        "Testing algo %s with blocklist of size %s", algo.__name__, blocklist.name
    )

    run_res: list[RunResult] = []

    for enhancement in ENHANCEMENTS:
        enable_radical = "radical" in enhancement
        enable_pinyin = "pinyin" in enhancement

        if not validate_test_case(enhancement, blocklist.name):
            continue

        logging.info(
            "Creating %s instance with %s enhancement (enable_radical=%s, enable_pinyin=%s)",
            algo.__name__,
            enhancement,
            enable_radical,
            enable_pinyin,
        )
        (instance, creation_time), measures = create_instance(
            algo, blocklist.patterns, enable_radical, enable_pinyin
        )
        logging.info(
            "Time taken to create instance with %s enhancement: %s",
            enhancement,
            creation_time,
        )
        # Remove first measure as it is the function call
        del measures[0]
        creation_mem = sum(mem.increment for mem in measures)
        logging.info(
            "Memory used to create instance with %s enhancement: %s",
            enhancement,
            creation_mem,
        )

        test_results: list[TestResult] = []
        for test in tests:
            logging.info("Test case %s", test.name)

            (res, test_time), measures = match_with_instance(instance, test.testcase)
            res = sorted([sorted(r) for r in res])

            logging.debug("Results: %s", res)
            if res != test.expected[enhancement]:
                logging.debug("Expected: %s", test.expected[enhancement])

                if enable_radical:
                    logging.debug("Radical map: %s", hasattr(instance, "radical_map"))
                if enable_pinyin:
                    logging.debug("Pinyin map: %s", hasattr(instance, "pinyin_map"))

                raise AssertionError("Results do not match")

            logging.info("Time taken for test case %s: %s", test.name, test_time)
            # Remove first measure as it is the function call
            del measures[0]
            test_mem = sum(mem.increment for mem in measures)
            logging.info("Memory used for test case %s: %s", test.name, test_mem)
            test_results.append(TestResult(test.name, test_time, test_mem))

        run_res.append(
            RunResult(enhancement, creation_time, creation_mem, test_results)
        )

    return AlgoResult(cast(AlgoName, algo.__name__), blocklist.name, run_res)


def run_tests() -> None:
    """Main function for running the tests."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    blocklist_dir = BASE_PATH / "blocklist"
    if not blocklist_dir.exists():
        raise FileNotFoundError("Blocklist directory does not exist")

    test_dir = BASE_PATH / "tests"
    if not test_dir.exists():
        raise FileNotFoundError("Test directory does not exist")

    test_res_dir = BASE_PATH / "tests" / "res"
    if not test_res_dir.exists():
        raise FileNotFoundError("Test result directory does not exist")

    output_dir = BASE_PATH / "results"
    output_dir.mkdir(exist_ok=True, parents=True)

    with open(
        output_dir / f"{time.strftime('%Y%m%d-%H%M%S')}.csv",
        "w",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "algo",
                "blocklist_name",
                "enhancement",
                "creation_time",
                "creation_mem",
            ]
            + [
                i
                for l in [
                    [f"test_{test_name}_time", f"test_{test_name}_mem"]
                    for test_name in TEST_NAMES
                ]
                for i in l
            ],
        )
        writer.writeheader()

        for blocklist_name in BLOCKLIST_NAMES:
            with open(
                blocklist_dir / f"blocklist_{blocklist_name}.txt",
                encoding="utf-8",
            ) as file:
                blocklist = file.read().splitlines()

            tests: list[TestCase] = []
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

                tests.append(TestCase(test_name, testcase, expected))

            for algo in ALGOS:
                res = test_algo(algo, Blocklist(blocklist_name, blocklist), tests)
                writer.writerows(res.to_csv_dicts())


if __name__ == "__main__":
    run_tests()
