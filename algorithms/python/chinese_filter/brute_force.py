"""
Naive algorithm for matching multiple strings by brute force.
"""

from chinese_filter._common import BaseAlgo, MatchResult, Pattern, TargetText


class BruteForce(BaseAlgo):
    """
    Naive algorithm for matching multiple strings by brute force.
    """

    NAME = "BruteForce"

    def __init__(self, patterns: list[Pattern]):
        """
        Create a new instance of the brute force algorithm.
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
            for i in range(len(text)):
                if i + len(pattern) > len(text):
                    break
                for j, pattern_char in enumerate(pattern):
                    if text[i + j] != pattern_char:
                        break
                else:
                    matches.append((i, pattern))

        return matches
