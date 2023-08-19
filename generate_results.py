"""Generate the results for the tests."""
import json
import logging

from benchmark import (
    BASE_PATH,
    BLOCKLIST_NAMES,
    TEST_NAMES,
    Blocklist,
    BlocklistName,
    TestCase,
    validate_test_case,
)
from src import ENHANCEMENTS, Native

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

blocklists: list[Blocklist] = []
tests: dict[BlocklistName, list[TestCase]] = {}

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
        blocklist = Blocklist(blocklist_name, file.read().splitlines())

    for enhancement in ENHANCEMENTS:
        enable_radical = "radical" in enhancement
        enable_pinyin = "pinyin" in enhancement

        if not validate_test_case(enhancement, blocklist_name):
            continue

        logging.info("Creating instance for %s - %s", blocklist_name, enhancement)
        instance = Native(
            blocklist.patterns,
            enable_radical=enable_radical,
            enable_pinyin=enable_pinyin,
        )

        for test_name in TEST_NAMES:
            with open(test_dir / f"{test_name}.txt", encoding="utf-8") as file:
                testcase = file.read()

            logging.info(
                "Generating results for %s - %s - %s",
                blocklist_name,
                enhancement,
                test_name,
            )
            res = instance.match(testcase)
            res = sorted([sorted(r) for r in res])
            dest_dir = test_res_dir / blocklist_name / enhancement / f"{test_name}.json"
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_dir, mode="w", encoding="utf-8") as file:
                json.dump(res, file, ensure_ascii=False, indent=4)
