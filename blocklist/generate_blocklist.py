"""This script generates the blocklist files from the raw text files."""

import glob
import random

# set the seed for the random number generator
random.seed(256)

NO_INCLUDE = ["文凭", "独立", "领导", "社会"]

blocklist_10 = sorted(
    [
        "新加坡",
        "世界联合书院",
        "国际文凭",
        "国际文凭组织",
        "国际文凭课程",
        "国际文凭学校",
        "国际文凭学院",
        "国际文凭大学预科",
        "国际文凭大学预科课程",
        "拓展论文",
    ]
)

# create a new set to store the words
blocklist_set = set(blocklist_10)

# For each of the source text files
for filename in glob.glob("raw/*.txt"):
    with open(filename, encoding="utf-8") as f:
        # Trim each line, remove punctuation and add to the set
        lines = [
            line.translate(
                str.maketrans(
                    "",
                    "",
                    ",?!%&-*$^~\\\"'[]{}，。？！：；“”‘’"
                    + "".join(chr(i) for i in range(0, 32))
                    + "".join(chr(i) for i in range(127, 256)),
                )
            ).strip()
            for line in f.read().splitlines()
        ]
        blocklist_set.update(line for line in lines if line and len(line) > 1)

blocklist_set.difference_update(NO_INCLUDE)
blocklist = sorted(blocklist_set)

if len(blocklist) == len(blocklist_10):
    raise ValueError("Blocklist is empty")

# output the words to blocklist_full.txt
with open("blocklist_full.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(blocklist))

# randomly choose 10 words from the set and output to blocklist_10.txt
# blocklist_10 = sorted(random.sample(blocklist, 10))
with open("blocklist_10.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(blocklist_10))

# randomly choose 100 words from the set and output to blocklist_100.txt
blocklist_100 = sorted(set(blocklist_10 + random.sample(blocklist, 90)))
with open("blocklist_100.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(blocklist_100))

# randomly choose 1000 words from the set and output to blocklist_1k.txt
blocklist_1k = sorted(set(blocklist_100 + random.sample(blocklist, 900)))
while len(blocklist_1k) < 1000:
    blocklist_1k.append(random.choice(blocklist))
with open("blocklist_1k.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(blocklist_1k))

# randomly choose 10000 words from the set and output to blocklist_10k.txt
blocklist_10k = sorted(set(blocklist_1k + random.sample(blocklist, 9000)))
while len(blocklist_10k) < 10000:
    blocklist_10k.append(random.choice(blocklist))
with open("blocklist_10k.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(blocklist_10k))

# Generate an optimised blocklist for the WM algorithm
# (lengths of patterns are similar to each other and have diverse prefixes)

# Sort the blocklist by length
blocklist_wm = sorted(blocklist, key=len)

# Only keep the first word with each prefix of length 2
prefixes: set[str] = set()
blocklist_wm_set = set()
for word in blocklist_wm:
    prefix = word[:2]
    if prefix not in prefixes:
        prefixes.add(prefix)
        blocklist_wm_set.add(word)

# Take the first 75% in terms of length between the shortest and longest words
blocklist_wm = sorted(
    set(
        sorted(blocklist_wm_set, key=len)[0 : len(blocklist_wm_set) * 3 // 4]
        + blocklist_10
    )
)

# output the words to blocklist_wm.txt
with open("blocklist_wm.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(blocklist_wm))
