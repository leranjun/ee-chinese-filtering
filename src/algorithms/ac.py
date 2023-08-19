"""This module implements an Aho-Corasick automaton for multi-pattern string matching in Chinese."""

from dataclasses import dataclass, field
from typing import Any

from . import BaseAlgo, MatchResult, Pattern, TargetText, byte_pos_to_char_pos

ByteIndex = int
NodeIndex = int

BYTE_SIZE = 256


@dataclass
class ACNode:
    """A node in the Aho-Corasick automaton."""

    # The pattern that ends at this node, if any
    patterns: list[Pattern] = field(default_factory=list)
    # The index of the child node in the nodes array
    children: dict[ByteIndex, NodeIndex] = field(default_factory=dict)


class AC(BaseAlgo):
    """An Aho-Corasick automaton."""

    MANUAL_INSERT = True

    def __init__(self, patterns: list[Pattern], *args: Any, **kwargs: Any) -> None:
        """Initialise the automaton with a list of patterns."""
        super().__init__(patterns, *args, **kwargs)

        self.root = ACNode()
        self.nodes = [self.root]
        self.fail: dict[NodeIndex, NodeIndex] = {}

        for pattern in patterns:
            self.insert(pattern)

        self.calculate_fail()

    def insert(self, pattern: Pattern) -> None:
        """Insert a key into the trie."""

        cur_idx: NodeIndex = 0
        for byte in pattern.encode("utf-8"):

            # Get the current node
            cur_node = self.nodes[cur_idx]

            # If the child node with this byte does not exist, create one
            if cur_node.children.get(byte, -1) == -1:
                # logging.debug("Creating child node")
                # Create a new node
                new_node = ACNode()
                # Append it to the list of nodes
                self.nodes.append(new_node)
                # Update the index of the child node with this byte
                cur_node.children[byte] = len(self.nodes) - 1

            # Move to the next node
            cur_idx = cur_node.children[byte]

        # cur_idx is now the last node, record the pattern here
        last_node = self.nodes[cur_idx]
        last_node.patterns.append(pattern)

        self._insert_pinyin(pattern)
        self._insert_radical(pattern)

    def calculate_fail(self) -> None:
        """Calculate the fail pointers using BFS."""

        queue = [0]
        while queue:
            parent = queue.pop(0)

            # For each child node of the current parent node
            for byte, child in self.nodes[parent].children.items():
                if child == -1:
                    # This child node does not exist
                    continue


                # Recursively traverse up the fail pointers until
                # we find a node that has a child node with this byte
                # (the "ancestor fail node")
                #
                # IMPORTANT: anc_fail_node must not be declared here
                # because when anc_fail is -1, anc_fail_node will be
                # the last node in the nodes array
                anc_fail = self.fail.get(parent, -1)
                while (
                    anc_fail != -1 and self.nodes[anc_fail].children.get(byte, -1) == -1
                ):
                    # The current node does not have a child node with this byte
                    # so we move on to its fail pointer
                    anc_fail = self.fail.get(anc_fail, -1)

                if anc_fail == -1:
                    # No possible fail node, set the fail pointer to the root
                    # logging.debug("Fail node not found")
                    self.fail[child] = 0
                else:
                    # Fail node found
                    anc_fail_node = self.nodes[anc_fail]

                    # Get the actual fail node from the ancestor fail node
                    cur_fail = anc_fail_node.children[byte]
                    cur_fail_node = self.nodes[cur_fail]

                    # Set the fail pointer
                    self.fail[child] = cur_fail
                    # Copy the patterns from the fail node to match
                    # the patterns that end at the current child node
                    self.nodes[child].patterns.extend(cur_fail_node.patterns)

                queue.append(child)

        # Set the fail pointer of the root node to itself
        self.fail[0] = 0

    def dump(self) -> list[str]:
        """Dump the nodes and fail pointers of the automaton."""
        super().dump()

        return [
            f"Node {idx}: {node}, fail: {self.fail.get(idx, -1)}"
            for idx, node in enumerate(self.nodes)
        ]

    def _match(self, text: TargetText) -> MatchResult:
        """Match the text with the patterns."""
        # Record the index of the current node
        cur_idx: NodeIndex = 0
        # Record the positions of the matches
        matches = MatchResult()

        text_bytes = text.encode("utf-8")
        for pos, byte in enumerate(text_bytes):

            # Recursively match the text using fail pointers
            # unless the current node is the root node
            while cur_idx != 0 and self.nodes[cur_idx].children.get(byte, -1) == -1:
                # The current node does not have a child node with this byte
                # so we move on to its fail pointer
                cur_idx = self.fail.get(cur_idx, -1)

            cur_node = self.nodes[cur_idx]

            if cur_node.children.get(byte, -1) != -1:
                # There is a child node with this byte
                cur_idx = cur_node.children[byte]
                child_node = self.nodes[cur_idx]

                if child_node.patterns:
                    # There is a pattern ending at this node, record the match
                    # logging.debug(
                    #     "Match: ending at position %d, patterns %s",
                    #     pos,
                    #     child_node.patterns,
                    # )
                    for pattern in child_node.patterns:
                        char_pos = byte_pos_to_char_pos(
                            pos, text_bytes, pattern.encode("utf-8")
                        )
                        matches.append(
                            (
                                char_pos,
                                pattern,
                            )
                        )
                else:
                    # There is no pattern ending at this node, but there may be
                    # patterns ending at the next ones
                    # logging.debug("Pattern may match, continue")
                    pass

            else:
                pass

        return matches
