"""Tests for dependency-first installation ordering."""

import unittest

from depgraph.order import installation_groups


class InstallationOrderTests(unittest.TestCase):
    """Verify ordering and strongly connected components."""

    def test_empty_graph(self):
        """An empty graph produces no groups."""
        self.assertEqual(installation_groups({}), [])

    def test_single_package(self):
        """A standalone package forms one group."""
        self.assertEqual(
            installation_groups({"A": []}),
            [["A"]],
        )

    def test_independent_packages(self):
        """Independent packages have deterministic ordering."""
        graph = {"C": [], "A": [], "B": []}
        self.assertEqual(
            installation_groups(graph),
            [["A"], ["B"], ["C"]],
        )

    def test_dependencies_first(self):
        """Dependencies must precede their dependents."""
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }
        self.assertEqual(
            installation_groups(graph),
            [["D"], ["B"], ["C"], ["A"]],
        )

    def test_cycle(self):
        """A cycle forms a single installation group."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }
        self.assertEqual(
            installation_groups(graph),
            [["A", "B", "C"]],
        )

    def test_cycle_with_dependency(self):
        """External dependencies precede a cyclic group."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["B", "D"],
            "D": [],
        }
        self.assertEqual(
            installation_groups(graph),
            [["D"], ["B", "C"], ["A"]],
        )

    def test_missing_leaf_node(self):
        """Include dependencies absent from graph keys."""
        graph = {"A": ["B"]}
        self.assertEqual(
            installation_groups(graph),
            [["B"], ["A"]],
        )

    def test_two_connected_cycles(self):
        """Order cyclic groups by their dependencies."""
        graph = {
            "A": ["B"],
            "B": ["A", "C"],
            "C": ["D"],
            "D": ["C"],
        }
        self.assertEqual(
            installation_groups(graph),
            [["C", "D"], ["A", "B"]],
        )


if __name__ == "__main__":
    unittest.main()
