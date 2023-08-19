"""This package implements multiple algorithms for multi-pattern string matching in Chinese."""

from typing import Literal, cast, get_args

from .algorithms import BaseAlgo, MatchResult, Pattern, TargetText
from .algorithms.ac import AC
from .algorithms.brute_force import BruteForce
from .algorithms.native import Native
from .algorithms.wm import WM

EnhancementType = Literal["naive", "pinyin", "radical", "radical_pinyin"]
ENHANCEMENTS = cast(tuple[EnhancementType, ...], get_args(EnhancementType))

AlgoType = BruteForce | Native | AC | WM
AlgoName = Literal["BruteForce", "Native", "AC", "WM"]
ALGOS = cast(tuple[type[AlgoType], ...], get_args(AlgoType))

__all__ = [
    "BaseAlgo",
    "MatchResult",
    "Pattern",
    "TargetText",
    "AC",
    "BruteForce",
    "Native",
    "WM",
    "EnhancementType",
    "ENHANCEMENTS",
    "AlgoType",
    "AlgoName",
    "ALGOS",
]
