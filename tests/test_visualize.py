"""Tests for dependency graph visualization."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from depgraph.visualize import render_graph


class VisualizationTests(unittest.TestCase):
    """Check Graphviz rendering and error handling."""

    def _dot_source(self, graph):
        """Capture the Graphviz input without running dot."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "graph.png"
            with patch(
                "depgraph.visualize.subprocess.run"
            ) as command:
                render_graph(graph, output)
                return command.call_args.kwargs["input"]

    @unittest.skipUnless(shutil.which("dot"), "Graphviz missing")
    def test_create_real_png(self):
        """Create an actual PNG with the correct signature."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "graph.png"
            result = render_graph(
                {"A": ["B"], "B": []}, output
            )
            self.assertEqual(result, output)
            self.assertTrue(output.is_file())
            self.assertEqual(
                output.read_bytes()[:8],
                b"\x89PNG\r\n\x1a\n",
            )

    def test_reject_wrong_extension(self):
        """Reject output formats other than PNG."""
        with self.assertRaises(ValueError):
            render_graph({"A": []}, "graph.svg")

    def test_normal_nodes_are_blue(self):
        """Normal packages should have a blue background."""
        source = self._dot_source({"A": ["B"], "B": []})
        self.assertIn('"A" [fillcolor="#e9f1ff"]', source)
        self.assertIn('"B" [fillcolor="#e9f1ff"]', source)

    def test_cycle_nodes_are_red(self):
        """Packages in cycles should be highlighted."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }
        source = self._dot_source(graph)

        for name in ("A", "B", "C"):
            self.assertIn(
                f'"{name}" [fillcolor="#ffe2e2"]',
                source,
            )

    def test_self_cycle_is_red(self):
        """Highlight a package depending on itself."""
        source = self._dot_source({"A": ["A"]})
        self.assertIn('"A" [fillcolor="#ffe2e2"]', source)

    def test_dependency_arrows(self):
        """Render dependency edges in the correct direction."""
        source = self._dot_source({"A": ["B"], "B": []})
        self.assertIn('"A" -> "B";', source)

    def test_escape_package_names(self):
        """Safely quote node names in Graphviz source."""
        target = 'c"d'
        source = self._dot_source({
            "a b": [target],
            target: [],
        })
        expected = (
            f'{json.dumps("a b")} -> '
            f'{json.dumps(target)};'
        )
        self.assertIn(expected, source)

    def test_missing_graphviz(self):
        """Report a missing Graphviz executable."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "graph.png"
            with patch(
                "depgraph.visualize.subprocess.run",
                side_effect=FileNotFoundError(),
            ):
                with self.assertRaises(RuntimeError):
                    render_graph({"A": []}, output)

    def test_graphviz_failure(self):
        """Report failures returned by Graphviz."""
        error = subprocess.CalledProcessError(
            1, ["dot"], stderr="bad input"
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "graph.png"
            with patch(
                "depgraph.visualize.subprocess.run",
                side_effect=error,
            ):
                with self.assertRaises(RuntimeError):
                    render_graph({"A": []}, output)


if __name__ == "__main__":
    unittest.main()
