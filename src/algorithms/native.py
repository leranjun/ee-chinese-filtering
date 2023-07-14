"""Algorithm using Python's built-in string search."""

from typing import Any

from . import BaseAlgo, MatchResult, Pattern, TargetText


class Native(BaseAlgo):
    """Algorithm using Python's built-in string search."""

    def __init__(self, patterns: list[Pattern], *args: Any, **kwargs: Any) -> None:
        """Create a new instance of the native algorithm."""
        super().__init__(patterns, *args, **kwargs)

        self.patterns = patterns

    def _match(self, text: TargetText) -> MatchResult:
        """Match a string against the blocklist."""
        matches = MatchResult()
        for pattern in self.patterns:
            idx = 0
            while idx < len(text):
                idx = text.find(pattern, idx)
                if idx == -1:
                    break
                matches.append((idx, pattern))
                idx += len(pattern)

        return matches
