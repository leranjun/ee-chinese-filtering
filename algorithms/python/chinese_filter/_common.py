"""This internal module contains shared classes and types across all algorithms."""

import logging
import warnings

Pattern = str
TargetText = str
MatchResult = list[tuple[int, Pattern]]


def byte_pos_to_char_pos(end_pos: int, text_bytes: bytes, pattern_bytes: bytes) -> int:
    """Convert a byte position to a character position."""
    start_pos = end_pos - len(pattern_bytes) + 1
    return len(text_bytes[:start_pos].decode())


class BaseAlgo:
    """Base class for multi-pattern string matching algorithms."""

    NAME = ""

    def __init__(self, patterns: list[Pattern]) -> None:
        """Create a new instance of the algorithm."""

    def dump(self) -> None:
        """Dump the internal state of the algorithm."""

    @staticmethod
    def match(text: TargetText) -> MatchResult:
        """Match a string against the blocklist."""

        logging.debug("Matching text: %s", text)

        if not isinstance(text, TargetText):
            raise TypeError("text must be a string")
        if text == "":
            warnings.warn("text is empty", RuntimeWarning)
            return MatchResult([(0, "")])

        return MatchResult()
