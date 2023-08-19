"""This module implements the Wu-Manber algorithm for multi-pattern string matching in Chinese."""

from typing import Any

from . import BaseAlgo, MatchResult, Pattern, TargetText, byte_pos_to_char_pos

Block = bytes


class WM(BaseAlgo):
    """The Wu-Manber algorithm."""

    MANUAL_INSERT = True

    def __init__(
        self, patterns: list[Pattern], *args: Any, block_size: int = 2, **kwargs: Any
    ) -> None:
        """Initialise the algorithm with a list of patterns."""
        super().__init__(patterns, *args, **kwargs)

        # The size of each block (B in the paper)
        self.block_size = block_size

        self.min_ptn_len = min(len(p.encode("utf-8")) for p in patterns)
        if self.min_ptn_len < self.block_size:
            raise ValueError(
                f"Patterns must be at least {self.block_size} characters long"
            )

        # A mapping of blocks to the number of characters to shift
        self.shift: dict[Block, int] = {}
        # A mapping of blocks to the patterns that end with the block
        self.hash: dict[Block, set[Pattern]] = {}
        # A mapping of blocks to the patterns that start with the block
        self.prefix: dict[Block, set[Pattern]] = {}

        for pattern in patterns:
            self.insert(pattern)

    def insert(self, pattern: Pattern) -> None:
        """Insert a pattern into the instance."""
        # Encode the pattern to bytes
        pattern_bytes = pattern.encode("utf-8")

        # For each group of BLOCK_SIZE characters from the first
        # min_ptn_len characters in the pattern, we calculate the
        # distance between the end of the group and the end of the
        # pattern, and store it in the shift table
        # e.g. for BLOCK_SIZE = 2, pattern = "abcde", we store
        # shift["ab"] = 3
        # shift["bc"] = 2
        # shift["cd"] = 1
        # shift["de"] = 0
        for i in range(self.min_ptn_len - self.block_size + 1):
            block = pattern_bytes[i : i + self.block_size]
            # logging.debug("Inserting block: %s", block)
            # When a block is already in the shift table, we keep the
            # smaller value
            self.shift[block] = min(
                self.shift.get(block, self.min_ptn_len),
                self.min_ptn_len - i - self.block_size,
            )

        # Insert the pattern to the hash table where the key is the
        # last BLOCK_SIZE characters of the first min_ptn_len characters
        # in the pattern
        # e.g. for BLOCK_SIZE = 2, pattern = "abcde", "abcc" and "abcd", we store
        # hash["cd"] = ["abcde", "abcd"]
        # hash["cc"] = ["abcc"]
        suffix_key = pattern_bytes[
            self.min_ptn_len - self.block_size : self.min_ptn_len
        ]
        self.hash.setdefault(suffix_key, set()).add(pattern)

        # Insert the pattern to the prefix table where the key is the
        # first BLOCK_SIZE characters of the pattern
        # e.g. for BLOCK_SIZE = 2, pattern = "abcde", "abcc" and "abcd", we store
        # prefix["ab"] = ["abcde", "abcc", "abcd"]
        prefix_key = pattern_bytes[: self.block_size]
        self.prefix.setdefault(prefix_key, set()).add(pattern)

        self._insert_pinyin(pattern)
        self._insert_radical(pattern)

    def dump(self) -> list[str]:
        """Dump the internal data structures."""
        super().dump()

        return [
            f"Shift table: {self.shift}",
            f"Hash table: {self.hash}",
            f"Prefix table: {self.prefix}",
        ]

    def _match(self, text: TargetText) -> MatchResult:
        """Match the patterns in the text."""
        text_bytes = text.encode("utf-8")
        matches = MatchResult()

        end_pos = self.min_ptn_len - 1
        while end_pos < len(text_bytes):
            # Get the current block
            end_block = text_bytes[end_pos - self.block_size + 1 : end_pos + 1]

            shift_val = self.shift.get(
                end_block,
                self.min_ptn_len - self.block_size + 1,
            )
            if shift_val != 0:
                end_pos += shift_val
                continue

            # Cross-check the hash table and the prefix table based on the current block
            start_pos = end_pos - self.min_ptn_len + 1
            start_block = text_bytes[start_pos : start_pos + self.block_size]
            potential_matches = self.hash.get(end_block, set()) & self.prefix.get(
                start_block, set()
            )
            for pattern in potential_matches:
                pattern_bytes = pattern.encode("utf-8")
                target_bytes = text_bytes[start_pos : start_pos + len(pattern_bytes)]
                if target_bytes == pattern_bytes:
                    matches.append(
                        (
                            byte_pos_to_char_pos(
                                start_pos + len(pattern_bytes) - 1,
                                text_bytes,
                                pattern_bytes,
                            ),
                            pattern,
                        )
                    )
                else:
                    pass

            end_pos += 1

        return matches
