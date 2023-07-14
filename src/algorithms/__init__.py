"""This module contains the base class for multi-pattern string matching algorithms."""

import itertools
import logging
import re
import warnings
from typing import Any, Optional, Sequence, TypeVar, cast, overload

from pinyintokenizer import PinyinTokenizer
from pypinyin import Style
from pypinyin import pinyin as to_pinyin
from text_unidecode import unidecode

from ..radical_dict import RADICAL_MAP

Pattern = str
TargetText = str
MatchResult = list[tuple[int, Pattern]]

Pinyin = str
Radical = str

T = TypeVar("T", bound=Sequence[Any])

__tokenizer = PinyinTokenizer()


def tokenize(text: Pinyin) -> tuple[list[Pinyin], list[str]]:
    """Tokenize a string of pinyin."""
    return cast(tuple[list[Pinyin], list[str]], __tokenizer.tokenize(text))


@overload
def get_combinations_from_sequence(seq: T, min_dist: int = 1) -> list[T]:
    ...


@overload
def get_combinations_from_sequence(
    seq: T, min_dist: int = 1, *, pattern: str
) -> list[tuple[T, str]]:
    ...


def get_combinations_from_sequence(
    seq: T, min_dist: int = 1, *, pattern: Optional[str] = None
) -> list[T] | list[tuple[T, str]]:
    """Get all the consecutive combinations from a list."""
    if pattern:
        return cast(
            list[tuple[T, str]],
            [
                (seq[i:j], pattern[i:j])
                for i in range(len(seq))
                for j in range(i + min_dist, len(seq) + 1)
            ],
        )

    return cast(
        list[T],
        [seq[i:j] for i in range(len(seq)) for j in range(i + min_dist, len(seq) + 1)],
    )


def byte_pos_to_char_pos(end_pos: int, text_bytes: bytes, pattern_bytes: bytes) -> int:
    """Convert a byte position to a character position."""
    start_pos = end_pos - len(pattern_bytes) + 1
    return len(text_bytes[:start_pos].decode())


class BaseAlgo:
    """Base class for multi-pattern string matching algorithms."""

    MANUAL_INSERT: bool = False

    def __init__(
        self,
        patterns: list[Pattern],
        enable_radical: bool = False,
        enable_pinyin: bool = False,
    ) -> None:
        """Create a new instance of the algorithm."""
        self.ENABLE_RADICAL = enable_radical  # pylint: disable=invalid-name
        self.ENABLE_PINYIN = enable_pinyin  # pylint: disable=invalid-name

        if self.ENABLE_PINYIN:
            self.pinyin_map: dict[tuple[Pinyin, ...], set[Pattern]] = {}

        if self.ENABLE_RADICAL:
            self.radical_map: dict[Radical, set[Pattern]] = {}

        if not self.MANUAL_INSERT and (self.ENABLE_PINYIN or self.ENABLE_RADICAL):
            for pattern in patterns:
                if self.ENABLE_PINYIN:
                    self._insert_pinyin(pattern)

                if self.ENABLE_RADICAL:
                    self._insert_radical(pattern)

    def _insert_pinyin(self, pattern: Pattern) -> None:
        """Insert a pattern into the pinyin map."""
        if not self.ENABLE_PINYIN:
            return

        # Only keep Chinese characters
        pattern = re.sub(r"[^\u4e00-\u9fa5]", "", pattern)

        # Convert the pattern to pinyin
        pattern_pinyin: list[list[Pinyin]] = to_pinyin(
            pattern, heteronym=True, style=Style.NORMAL
        )

        full_combinations: list[tuple[Pinyin, ...]] = list(
            itertools.product(*pattern_pinyin)
        )

        # Combinations is of the form [(tuple of pinyin, corresponding pattern), ...]
        combinations = list(
            {
                combination
                for full_combination in full_combinations
                for combination in get_combinations_from_sequence(
                    full_combination, pattern=pattern
                )
            }
        )

        self.pinyin_map.update(
            {
                combination[0]: self.pinyin_map.get(combination[0], set()).union(
                    {combination[1]}
                )
                for combination in combinations
            }
        )

    def _insert_radical(self, pattern: Pattern) -> None:
        """Insert a pattern into the radical map."""
        if not self.ENABLE_RADICAL:
            return

        # Only keep Chinese characters
        pattern = re.sub(r"[^\u4e00-\u9fa5]", "", pattern)

        self.radical_map.update(
            {
                method: self.radical_map.get(method, set()).union({char})
                for char in pattern
                if char in RADICAL_MAP
                for method in RADICAL_MAP[char]
            }
        )

    def dump(self) -> None:
        """Dump the internal state of the algorithm."""
        logging.debug("Dumping %s", self.__class__.__name__)

        if self.ENABLE_PINYIN:
            logging.debug("Pinyin map: %s", self.pinyin_map)

        if self.ENABLE_RADICAL:
            logging.debug("Radical map: %s", self.radical_map)

    def preprocess(self, text: TargetText) -> list[str]:
        """Preprocess the text before matching."""

        if not isinstance(text, TargetText):
            raise TypeError("text must be a string")

        if text == "":
            warnings.warn("text is empty", RuntimeWarning)
            return []

        # Normalize non-Chinese characters
        text = re.sub(
            r"[^\u4e00-\u9fff]+", lambda m: unidecode(m.group()), text.lower()
        )

        res = [text]

        if self.ENABLE_RADICAL and len(self.radical_map) > 0:
            unique_radicals = "".join(
                set(char for key in self.radical_map for char in key)
            )
            logging.debug("Unique radicals: %s", unique_radicals)

            # Replace any potential radicals in TargetText
            potential_radicals: set[Radical] = set(
                re.findall(rf"[{unique_radicals}]{{2,}}", text)
            )
            logging.debug("Potential radicals: %s", potential_radicals)
            for radical_group in potential_radicals:
                radical_combinations = get_combinations_from_sequence(radical_group, 2)
                logging.debug("Radical combinations: %s", radical_combinations)
                for r_combination in radical_combinations:
                    if r_combination not in self.radical_map:
                        continue

                    potential_chars = self.radical_map[r_combination]
                    logging.debug("Radical hit: %s %s", r_combination, potential_chars)
                    res.extend(
                        [
                            text.replace(r_combination, character)
                            for character in potential_chars
                        ]
                    )

        if self.ENABLE_PINYIN and len(self.pinyin_map) > 0:
            # Recognise any potential pinyin in TargetText
            potential_pinyin: list[str] = re.findall(r"(?:[a-z]+ ?)+", text)
            logging.debug("Potential pinyin: %s", potential_pinyin)
            for pinyin_group in potential_pinyin:
                pinyin_list = tokenize(pinyin_group)[0]
                pinyin_list_stripped = tokenize("".join(pinyin_group.split()))[0]
                logging.debug("Pinyin list: %s", pinyin_list)

                pinyin_combinations = get_combinations_from_sequence(
                    pinyin_list
                ) + get_combinations_from_sequence(pinyin_list_stripped)
                logging.debug("Pinyin combinations: %s", pinyin_combinations)
                for _combination in pinyin_combinations:
                    p_combination = tuple(_combination)
                    if p_combination not in self.pinyin_map:
                        continue

                    potential_chars = self.pinyin_map[p_combination]
                    logging.debug(
                        "Pinyin hit: %s %s",
                        p_combination,
                        potential_chars,
                    )
                    res.extend(
                        [
                            re.sub(
                                r"\s*".join(map(re.escape, p_combination)),
                                character,
                                text,
                            )
                            for character in potential_chars
                        ]
                    )

        return res

    def _match(self, text: TargetText) -> MatchResult:
        """Match a string against the blocklist."""
        raise NotImplementedError

    def match(self, original: TargetText) -> list[MatchResult]:
        """Match a string against the blocklist."""
        logging.debug("Matching text: %s", original)

        res: list[MatchResult] = []
        for text in self.preprocess(original):
            res.append(self._match(text))

        return res


__all__ = [
    "BaseAlgo",
    "Pattern",
    "TargetText",
    "MatchResult",
    "Pinyin",
    "Radical",
    "byte_pos_to_char_pos",
]
