"""Benchmarking script for the algorithms."""

import json
import logging
import time
from dataclasses import dataclass
from typing import Callable, ParamSpec, TypeVar, cast

from chinese_filter import AC, WM, BruteForce, MatchResult, Native, Pattern, TargetText
from chinese_filter._common import BaseAlgo
from memory_profiler import profile

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_PATH = "../../../"
TEST_NAMES = ["1_short", "2_medium", "3_long"]
BLOCKLIST_SIZES = ["10", "100", "1k", "10k", "full", "wm"]

Name = str
Time = float
BlocklistInfo = tuple[Name, list[Pattern]]
TestsInfo = list[tuple[Name, TargetText, MatchResult]]
TestResults = list[tuple[Name, MatchResult, Time]]


@dataclass
class RunResult:
    """Dataclass for storing the results of a test."""

    instance_name: Name
    blocklist_size: Name
    creation_time: Time
    test_results: TestResults

    def __str__(self) -> str:
        return (
            "========================================\n"
            + f"Algorithm: {self.instance_name}\n"
            + f"Blocklist size: {self.blocklist_size}\n"
            + f"Creation time: {self.creation_time}\n"
            + "\n"
            + "\n".join(
                f"Test case: {test_result[0]}\n"
                # + f"Results: {test_result[1]}\n"
                + f"Time used: {test_result[2]}\n"
                for test_result in self.test_results
            )
            + "========================================\n"
        )


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
    create_instance: Callable[[type[BaseAlgo], list[Pattern]], tuple[BaseAlgo, Time]],
    match_with_instance: Callable[[BaseAlgo, TargetText], tuple[MatchResult, Time]],
) -> RunResult:
    """Test a given algorithm with a given blocklist and tests."""
    logging.info("Testing blocklist of size %s", blocklist_info[0])

    logging.info("Creating %s instance", algo.NAME)
    instance, creation_time = create_instance(algo, blocklist_info[1])
    logging.info("Time taken to create %s instance: %s", algo.NAME, creation_time)

    test_results = TestResults()
    for i, test in enumerate(tests_info):
        logging.info("Test case %s", i + 1)

        res, test_time = match_with_instance(instance, test[1])

        logging.info("Results: %s", res)
        if sorted(res) != test[2]:
            raise AssertionError("Results do not match")

        logging.info("Time taken for test case %d: %s", i + 1, test_time)
        test_results.append((test[0], res, test_time))

    del instance

    return RunResult(algo.NAME, blocklist_info[0], creation_time, test_results)


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

    with open(f"{BASE_PATH}results/python.txt", "w", encoding="utf-8") as res_file:
        P = ParamSpec("P")  # pylint: disable=invalid-name
        R = TypeVar("R")

        def prof(func: Callable[P, R]) -> Callable[P, R]:
            """Decorator for profiling a function."""
            return cast(Callable[P, R], profile(func, stream=res_file, precision=4))

        create_instance = prof(_create_instance)
        match_with_instance = prof(_match_with_instance)

        for size in BLOCKLIST_SIZES:
            with open(
                f"{BASE_PATH}blocklist/blocklist_{size}.txt", encoding="utf-8"
            ) as file:
                blocklist = file.read().splitlines()

            for algo in [BruteForce, Native, AC, WM]:
                # for algo in [AC]:
                res = test_algo(
                    algo,
                    (size, blocklist),
                    tests,
                    create_instance,
                    match_with_instance,
                )
                res_file.write(str(res))


if __name__ == "__main__":
    run_tests()
