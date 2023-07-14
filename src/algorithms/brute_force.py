"""Naive algorithm for matching multiple strings by brute force."""

from typing import Any

from . import BaseAlgo, MatchResult, Pattern, TargetText


class BruteForce(BaseAlgo):
    """Naive algorithm for matching multiple strings by brute force."""

    def __init__(self, patterns: list[Pattern], *args: Any, **kwargs: Any) -> None:
        """Create a new instance of the brute force algorithm."""
        super().__init__(patterns, *args, **kwargs)

        self.patterns = patterns

    def _match(self, text: TargetText) -> MatchResult:
        """Match a string against the blocklist."""
        matches = MatchResult()
        for pattern in self.patterns:
            for i in range(len(text)):
                if i + len(pattern) > len(text):
                    break
                for j, pattern_char in enumerate(pattern):
                    if text[i + j] != pattern_char:
                        break
                else:
                    matches.append((i, pattern))

        return matches
