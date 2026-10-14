"""Render dependency graphs as PNG images."""

import json
import subprocess
from pathlib import Path

from depgraph.order import installation_groups


def render_graph(graph, output):
    """Draw a dependency graph using Graphviz."""
    output_path = Path(output)

    if output_path.suffix.lower() != ".png":
        raise ValueError("Output must be a PNG file")

    nodes = set(graph)
    for dependencies in graph.values():
        nodes.update(dependencies)

    groups = installation_groups(graph)

    cyclic = set()
    for group in groups:
        if len(group) > 1:
            cyclic.update(group)
        elif group and group[0] in graph.get(group[0], []):
            cyclic.update(group)

    lines = [
        "digraph Dependencies {",
        '  graph [rankdir=LR, bgcolor="white"];',
        '  node [shape=box, style="rounded,filled"];',
        '  edge [color="#526780"];',
    ]

    for name in sorted(nodes):
        color = "#ffe2e2" if name in cyclic else "#e9f1ff"
        identifier = json.dumps(name)
        lines.append(
            f'  {identifier} [fillcolor="{color}"];'
        )

    for name in sorted(graph):
        for dependency in sorted(set(graph[name])):
            source = json.dumps(name)
            target = json.dumps(dependency)
            lines.append(f"  {source} -> {target};")

    lines.append("}")

    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    try:
        subprocess.run(
            ["dot", "-Tpng", "-o", str(output_path)],
            input="\n".join(lines),
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "Graphviz is not installed"
        ) from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Graphviz error: {error.stderr}"
        ) from error

    return output_path
