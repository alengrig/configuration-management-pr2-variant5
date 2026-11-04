"""Tests for Mermaid diagram generation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from depgraph.mermaid import mermaid_source
from depgraph.visualize import render_graph


class MermaidTests(unittest.TestCase):
    """Check Mermaid nodes, edges and cycle styles."""

    def test_nodes_and_edges(self):
        """Generate a simple dependency diagram."""
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }

        text = mermaid_source(graph)

        self.assertTrue(text.startswith("flowchart LR"))
        self.assertIn('n0["A"]', text)
        self.assertIn('n3["D"]', text)
        self.assertIn("n0 --> n1", text)
        self.assertIn("n0 --> n2", text)
        self.assertIn("n1 --> n3", text)
        self.assertIn("n2 --> n3", text)

    def test_missing_leaf_node(self):
        """Include dependencies absent from graph keys."""
        text = mermaid_source({"A": ["B"]})

        self.assertIn('n1["B"]', text)
        self.assertIn("n0 --> n1", text)

    def test_cycle_nodes_are_colored(self):
        """Highlight all packages in a cycle."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }

        text = mermaid_source(graph)

        for index in range(3):
            self.assertIn(
                f"style n{index} fill:#ffe2e2",
                text,
            )

    def test_self_cycle_is_colored(self):
        """Highlight self-referencing dependencies."""
        text = mermaid_source({"A": ["A"]})

        self.assertIn("style n0 fill:#ffe2e2", text)

    def test_normal_graph_has_no_cycle_styles(self):
        """Do not highlight packages without cycles."""
        text = mermaid_source({
            "A": ["B"],
            "B": [],
        })

        self.assertNotIn("style n0", text)
        self.assertNotIn("style n1", text)

    def test_escape_special_characters(self):
        """Escape special characters in package labels."""
        text = mermaid_source({
            "<A&B>": ['b"x'],
        })

        self.assertIn("#lt;A#amp;B#gt;", text)
        self.assertIn("b#quot;x", text)

    def test_duplicate_edges(self):
        """Do not generate repeated arrows."""
        text = mermaid_source({
            "A": ["B", "B"],
            "B": [],
        })

        self.assertEqual(text.count("n0 --> n1"), 1)

    def test_render_creates_mermaid_file(self):
        """Save Mermaid text alongside a PNG output."""
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "graph.png"

            with patch(
                "depgraph.visualize.subprocess.run"
            ):
                render_graph({"A": ["B"], "B": []}, output)

            mermaid_file = output.with_suffix(".mmd")

            self.assertTrue(mermaid_file.is_file())
            self.assertIn(
                "flowchart LR",
                mermaid_file.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
