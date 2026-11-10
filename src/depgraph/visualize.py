"""Render dependency graphs as PNG images."""

import json
import subprocess
from pathlib import Path

from depgraph.order import installation_groups
from depgraph.mermaid import mermaid_source


def validate_output_path(output):
    """Validate PNG output path and create parent directory."""
    output_path = Path(output)

    if output_path.suffix.lower() != ".png":
        raise ValueError("Output must be a PNG file")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def collect_nodes(graph):
    """Return all nodes from graph keys and dependency values."""
    nodes = set(graph)

    for dependencies in graph.values():
        nodes.update(dependencies)

    return nodes


def is_self_cycle(graph, package):
    """Return True when a package depends on itself."""
    return package in graph.get(package, [])


def collect_cyclic_nodes(graph):
    """Return names of nodes that belong to cycles."""
    cyclic = set()
    groups = installation_groups(graph)

    for group in groups:
        if len(group) > 1:
            cyclic.update(group)
        elif len(group) == 1 and is_self_cycle(graph, group[0]):
            cyclic.update(group)

    return cyclic


def node_fill_color(name, cyclic):
    """Return node fill color based on cycle membership."""
    if name in cyclic:
        return "#ffe2e2"
    return "#e9f1ff"


def build_dot_header():
    """Return standard DOT header lines."""
    return [
        "digraph Dependencies {",
        '  graph [rankdir=LR, bgcolor="white"];',
        '  node [shape=box, style="rounded,filled"];',
        '  edge [color="#526780"];',
    ]


def append_node_lines(lines, nodes, cyclic):
    """Append DOT lines describing graph nodes."""
    for name in sorted(nodes):
        identifier = json.dumps(name)
        color = node_fill_color(name, cyclic)
        lines.append(f'  {identifier} [fillcolor="{color}"];')


def append_edge_lines(lines, graph):
    """Append DOT lines describing graph edges."""
    for name in sorted(graph):
        source = json.dumps(name)

        for dependency in sorted(set(graph[name])):
            target = json.dumps(dependency)
            lines.append(f"  {source} -> {target};")


def build_dot_source(graph):
    """Build complete DOT source code for Graphviz."""
    nodes = collect_nodes(graph)
    cyclic = collect_cyclic_nodes(graph)
    lines = build_dot_header()

    append_node_lines(lines, nodes, cyclic)
    append_edge_lines(lines, graph)
    lines.append("}")

    return "\n".join(lines)


def run_graphviz(dot_source, output_path):
    """Run Graphviz dot command and write PNG output."""
    try:
        subprocess.run(
            ["dot", "-Tpng", "-o", str(output_path)],
            input=dot_source,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Graphviz is not installed") from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Graphviz error: {error.stderr}"
        ) from error


def write_mermaid_file(graph, output_path):
    """Write Mermaid source рядом с PNG-файлом."""
    mermaid_path = output_path.with_suffix(".mmd")
    mermaid_path.write_text(
        mermaid_source(graph),
        encoding="utf-8",
    )


def render_graph(graph, output):
    """Draw a dependency graph using Graphviz."""
    output_path = validate_output_path(output)
    dot_source = build_dot_source(graph)
    run_graphviz(dot_source, output_path)
    write_mermaid_file(graph, output_path)
    return output_path