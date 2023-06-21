"""
This package implements multiple algorithms for multi-pattern string matching in Chinese.
"""

from chinese_filter._common import MatchResult, Pattern, TargetText
from chinese_filter.ac import AC
from chinese_filter.brute_force import BruteForce
from chinese_filter.native import Native
from chinese_filter.wm import WM

__all__ = ["MatchResult", "Pattern", "TargetText", "AC", "BruteForce", "Native", "WM"]
