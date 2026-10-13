"""Check recursive dependency traversal and test repositories."""

import unittest

from depgraph.graph import GraphError, build_graph
from depgraph.graph import parse_test_repository, ubuntu_dependencies


class GraphTests(unittest.TestCase):
    """Verify parser, DFS, and Ubuntu dependency extraction."""

    def test_parse_simple_repository(self):
        """Read adjacency lists and packages without dependencies."""
        repository = parse_test_repository("A: B C\nB:\nC:\n")
        self.assertEqual(repository, {"A": ["B", "C"], "B": [], "C": []})

    def test_ignore_comments_and_empty_lines(self):
        """Ignore comments and blank lines in a test repository."""
        repository = parse_test_repository("# note\n\nA: B\n B: \n")
        self.assertEqual(repository, {"A": ["B"], "B": []})

    def test_reject_duplicate_package(self):
        """Reject duplicate package definitions."""
        with self.assertRaises(GraphError):
            parse_test_repository("A:\nA:\n")

    def test_reject_undefined_package(self):
        """Reject dependencies that were not defined."""
        with self.assertRaises(GraphError):
            parse_test_repository("A: B\n")

    def test_reject_lowercase_name(self):
        """Require uppercase package names in test mode."""
        with self.assertRaises(GraphError):
            parse_test_repository("alpha:\n")

    def test_reject_empty_repository(self):
        """Reject empty test repositories."""
        with self.assertRaises(GraphError):
            parse_test_repository("\n # comment\n")

    def test_dfs_transitive_dependencies(self):
        """Visit dependencies at every reachable depth."""
        repo = parse_test_repository("A: B C\nB: D\nC: D\nD:\n")
        graph, cycles = build_graph("A", repo.__getitem__)
        self.assertEqual(set(graph), {"A", "B", "C", "D"})
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(cycles, [])

    def test_dfs_cycle(self):
        """Report cycles without infinite recursion."""
        repo = parse_test_repository("A: B\nB: C\nC: A\n")
        graph, cycles = build_graph("A", repo.__getitem__)
        self.assertEqual(len(graph), 3)
        self.assertEqual(cycles, [["A", "B", "C", "A"]])

    def test_dfs_shared_dependency(self):
        """Process shared descendants only once."""
        repo = parse_test_repository("A: B C\nB: D\nC: D\nD:\n")
        calls = []

        def children(name):
            calls.append(name)
            return repo[name]

        build_graph("A", children)
        self.assertEqual(calls.count("D"), 1)

    def test_dfs_self_cycle(self):
        """Detect a package depending on itself."""
        graph, cycles = build_graph("A", lambda name: [name])
        self.assertEqual(graph, {"A": ["A"]})
        self.assertEqual(cycles, [["A", "A"]])

    def test_ubuntu_alternatives(self):
        """Choose an available alternative and ignore version text."""
        packages = {
            "alpha": {"depends": "beta (>= 2), gamma | delta"},
            "beta": {},
            "delta": {},
        }
        children, missing = ubuntu_dependencies(packages, "alpha")
        self.assertEqual(children, ["beta", "delta"])
        self.assertEqual(missing, [])

    def test_ubuntu_unresolved_requirement(self):
        """Report dependency names absent from the index."""
        packages = {"alpha": {"depends": "awk"}}
        children, missing = ubuntu_dependencies(packages, "alpha")
        self.assertEqual(children, [])
        self.assertEqual(missing, ["awk"])

    def test_ubuntu_no_dependencies(self):
        """Return empty lists for a standalone package."""
        self.assertEqual(ubuntu_dependencies({"alpha": {}}, "alpha"), ([], []))

    def test_ubuntu_no_duplicate_children(self):
        """List a repeated dependency once."""
        packages = {"alpha": {"depends": "beta, beta"}, "beta": {}}
        children, missing = ubuntu_dependencies(packages, "alpha")
        self.assertEqual(children, ["beta"])
        self.assertEqual(missing, [])


    def test_build_virtual_providers(self):
        """Find packages declaring the same virtual name."""
        from depgraph.graph import build_providers

        packages = {
            "mawk": {"provides": "awk"},
            "gawk": {"provides": "awk"},
        }

        providers = build_providers(packages)
        self.assertEqual(providers["awk"], ["gawk", "mawk"])

    def test_resolve_virtual_dependency(self):
        """Resolve a virtual dependency through its provider."""
        from depgraph.graph import build_providers

        packages = {
            "base-files": {"depends": "awk"},
            "mawk": {"provides": "awk"},
        }

        providers = build_providers(packages)
        children, missing = ubuntu_dependencies(
            packages, "base-files", providers
        )

        self.assertEqual(children, ["mawk"])
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
