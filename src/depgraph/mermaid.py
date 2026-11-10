"""Generate Mermaid diagrams for dependency graphs."""

from depgraph.order import installation_groups


def collect_nodes(graph):
    """Collect all package names from the dependency graph."""
    nodes = set(graph)

    for dependencies in graph.values():
        nodes.update(dependencies)

    return sorted(nodes)


def escape_label(name):
    """Escape special characters in Mermaid node labels."""
    return (
        name.replace("&", "#amp;")
        .replace('"', "#quot;")
        .replace("<", "#lt;")
        .replace(">", "#gt;")
    )


def append_nodes(lines, names, identifiers):
    """Add Mermaid node definitions."""
    for name in names:
        label = escape_label(name)
        lines.append(f'    {identifiers[name]}["{label}"]')


def append_edges(lines, graph, identifiers):
    """Add dependency arrows to the Mermaid diagram."""
    for name in sorted(graph):
        for dependency in sorted(set(graph[name])):
            lines.append(
                f"    {identifiers[name]} --> "
                f"{identifiers[dependency]}"
            )


def is_cyclic_group(group, graph):
    """Check whether a group contains a dependency cycle."""
    if len(group) > 1:
        return True

    if not group:
        return False

    package = group[0]
    return package in graph.get(package, [])


def append_cycle_styles(lines, graph, identifiers):
    """Highlight packages belonging to dependency cycles."""
    for group in installation_groups(graph):
        if not is_cyclic_group(group, graph):
            continue

        for name in group:
            lines.append(
                f"    style {identifiers[name]} "
                "fill:#ffe2e2,stroke:#ac6666"
            )


def mermaid_source(graph):
    """Create a Mermaid flowchart from dependencies."""
    names = collect_nodes(graph)

    identifiers = {
        name: f"n{index}"
        for index, name in enumerate(names)
    }

    lines = ["flowchart LR"]

    append_nodes(lines, names, identifiers)
    append_edges(lines, graph, identifiers)
    append_cycle_styles(lines, graph, identifiers)

    return "\n".join(lines) + "\n"
