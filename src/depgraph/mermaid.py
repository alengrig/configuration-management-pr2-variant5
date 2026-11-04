"""Generate Mermaid diagrams for dependency graphs."""

from depgraph.order import installation_groups


def mermaid_source(graph):
    """Create a Mermaid flowchart from dependencies."""
    nodes = set(graph)

    for dependencies in graph.values():
        nodes.update(dependencies)

    names = sorted(nodes)
    identifiers = {
        name: f"n{index}"
        for index, name in enumerate(names)
    }

    lines = ["flowchart LR"]

    for name in names:
        label = (
            name.replace("&", "#amp;")
            .replace('"', "#quot;")
            .replace("<", "#lt;")
            .replace(">", "#gt;")
        )
        lines.append(
            f'    {identifiers[name]}["{label}"]'
        )

    for name in sorted(graph):
        for dependency in sorted(set(graph[name])):
            lines.append(
                f"    {identifiers[name]} --> "
                f"{identifiers[dependency]}"
            )

    for group in installation_groups(graph):
        is_cycle = len(group) > 1 or (
            bool(group)
            and group[0] in graph.get(group[0], [])
        )

        if is_cycle:
            for name in group:
                lines.append(
                    f"    style {identifiers[name]} "
                    "fill:#ffe2e2,stroke:#ac6666"
                )

    return "\n".join(lines) + "\n"
