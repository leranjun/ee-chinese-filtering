"""This package implements multiple algorithms for multi-pattern string matching in Chinese."""

from .algorithms import BaseAlgo, MatchResult, Pattern, TargetText
from .algorithms.ac import AC
from .algorithms.brute_force import BruteForce
from .algorithms.native import Native
from .algorithms.wm import WM

__all__ = [
    "BaseAlgo",
    "MatchResult",
    "Pattern",
    "TargetText",
    "AC",
    "BruteForce",
    "Native",
    "WM",
]
