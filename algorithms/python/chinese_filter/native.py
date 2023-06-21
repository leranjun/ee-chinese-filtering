"""
Algorithm using Python's built-in string search.
"""

from chinese_filter._common import BaseAlgo, MatchResult, Pattern, TargetText


class Native(BaseAlgo):
    """
    Algorithm using Python's built-in string search.
    """

    NAME = "Native"

    def __init__(self, patterns: list[Pattern]):
        """
        Create a new instance of the native algorithm.
        """

        self.patterns = patterns

    def match(self, text: TargetText) -> MatchResult:
        """
        Match a string against the blocklist.
        """
        check = super().match(text)
        if len(check) > 0:
            return MatchResult()

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
