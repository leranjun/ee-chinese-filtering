"""Benchmarking script for the algorithms."""

import csv
import json
import logging
import time
from dataclasses import dataclass
from typing import Callable, cast

from src import (AC, WM, BaseAlgo, BruteForce, MatchResult, Native, Pattern,
                 TargetText)
from src.profile import MemMeasure, profile

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_PATH = "./"
TEST_NAMES = ["1_short", "2_medium", "3_long"]
BLOCKLIST_SIZES = ["10", "100", "1k", "10k", "full", "wm"]

Name = str
Time = float
Mem = float
BlocklistInfo = tuple[Name, list[Pattern]]
TestsInfo = list[tuple[Name, TargetText, MatchResult]]
TestResults = list[tuple[Name, MatchResult, Time, Mem]]


@dataclass
class RunResult:
    """Dataclass for storing the results of a test."""

    algo: Name
    blocklist_size: Name
    creation_time: Time
    creation_mem: Mem
    test_results: TestResults

    def __str__(self) -> str:
        return (
            "========================================\n"
            + f"Algorithm: {self.algo}\n"
            + f"Blocklist size: {self.blocklist_size}\n"
            + f"Creation time: {self.creation_time}\n"
            + "\n"
            + "\n".join(
                f"Test case: {test_result[0]}\n"
                # + f"Results: {test_result[1]}\n"
                + f"Time used: {test_result[2]}\n" + f"Memory used: {test_result[3]}\n"
                for test_result in self.test_results
            )
            + "========================================\n"
        )

    def to_csv_dict(self) -> dict[str, str]:
        """Convert the results to a dictionary for CSV export."""
        res: dict[str, str] = {
            "algo": self.algo,
            "blocklist_size": self.blocklist_size,
            "creation_time": str(self.creation_time),
            "creation_mem": str(self.creation_mem),
        }

        for test_result in self.test_results:
            res[f"test_{test_result[0]}_time"] = str(test_result[2])
            res[f"test_{test_result[0]}_mem"] = str(test_result[3])

        return res


def _create_instance(
    algo: type[BaseAlgo], blocklist_content: list[Pattern]
) -> tuple[BaseAlgo, Time]:
    """Create an instance of a given algorithm."""
    time_start = time.time()
    instance = algo(blocklist_content)
    time_end = time.time()
    return instance, time_end - time_start


def _match_with_instance(
    instance: BaseAlgo, text: TargetText
) -> tuple[MatchResult, Time]:
    """Match a given test case with a given instance of an algorithm."""
    time_start = time.time()
    res = instance.match(text)
    time_end = time.time()
    return res, time_end - time_start


def test_algo(
    algo: type[BaseAlgo],
    blocklist_info: BlocklistInfo,
    tests_info: TestsInfo,
    create_instance: Callable[
        [type[BaseAlgo], list[Pattern]],
        tuple[tuple[BaseAlgo, Time], list[tuple[int, MemMeasure]]],
    ],
    match_with_instance: Callable[
        [BaseAlgo, TargetText],
        tuple[tuple[MatchResult, Time], list[tuple[int, MemMeasure]]],
    ],
) -> RunResult:
    """Test a given algorithm with a given blocklist and tests."""
    logging.info("Testing blocklist of size %s", blocklist_info[0])

    logging.info("Creating %s instance", algo.__name__)
    (instance, creation_time), measures = create_instance(algo, blocklist_info[1])
    logging.info("Time taken to create %s instance: %s", algo.__name__, creation_time)
    # Remove first measure as it is the function call
    del measures[0]
    creation_mem = sum(mem[1][0] for mem in measures)
    logging.info("Memory used to create %s instance: %s", algo.__name__, creation_mem)

    test_results = TestResults()
    for i, test in enumerate(tests_info):
        logging.info("Test case %s", i + 1)

        (res, test_time), measures = match_with_instance(instance, test[1])

        logging.info("Results: %s", res)
        if sorted(res) != test[2]:
            raise AssertionError("Results do not match")

        logging.info("Time taken for test case %d: %s", i + 1, test_time)
        # Remove first measure as it is the function call
        del measures[0]
        test_mem = sum(mem[1][0] for mem in measures)
        logging.info("Memory used for test case %d: %s", i + 1, test_mem)
        test_results.append((test[0], res, test_time, test_mem))

    del instance

    return RunResult(
        algo=algo.__name__,
        blocklist_size=blocklist_info[0],
        creation_time=creation_time,
        creation_mem=creation_mem,
        test_results=test_results,
    )


def run_tests() -> None:
    """Main function for running the tests."""
    tests = TestsInfo()
    for test_name in TEST_NAMES:
        with open(f"{BASE_PATH}tests/{test_name}.txt", encoding="utf-8") as file:
            test_case = file.read()
        with open(f"{BASE_PATH}tests/res/{test_name}.json", encoding="utf-8") as file:
            test_res = cast(
                MatchResult, sorted([tuple(res) for res in json.load(file)])
            )
        tests.append((test_name, test_case, test_res))

    with open(
        f"{BASE_PATH}results/{time.strftime('%Y%m%d-%H%M%S')}.csv",
        "w",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["algo", "blocklist_size", "creation_time", "creation_mem"]
            + [
                _i
                for _ in [[f"test_{i}_time", f"test_{i}_mem"] for i in TEST_NAMES]
                for _i in _
            ],
        )
        writer.writeheader()

        for size in BLOCKLIST_SIZES:
            with open(
                f"{BASE_PATH}blocklist/blocklist_{size}.txt", encoding="utf-8"
            ) as file:
                blocklist = file.read().splitlines()

            for algo in [BruteForce, Native, AC, WM]:
                # for algo in [AC]:
                create_instance = profile(_create_instance, backend="psutil_uss")
                match_with_instance = profile(_match_with_instance, backend="psutil_uss")

                res = test_algo(
                    algo,
                    (size, blocklist),
                    tests,
                    create_instance,
                    match_with_instance,
                )

                writer.writerow(res.to_csv_dict())


if __name__ == "__main__":
    run_tests()
