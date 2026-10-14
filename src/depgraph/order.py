"""Determine dependency-first installation groups."""


def installation_groups(graph):
    """Order dependencies first and keep cycles together."""
    nodes = set(graph)
    for dependencies in graph.values():
        nodes.update(dependencies)

    adjacency = {
        node: sorted(set(graph.get(node, []))) for node in nodes
    }
    indices = {}
    lowlinks = {}
    stack = []
    active = set()
    components = []
    next_index = 0

    def visit(node):
        """Find strongly connected components using DFS."""
        nonlocal next_index
        indices[node] = next_index
        lowlinks[node] = next_index
        next_index += 1
        stack.append(node)
        active.add(node)

        for dependency in adjacency[node]:
            if dependency not in indices:
                visit(dependency)
                lowlinks[node] = min(
                    lowlinks[node], lowlinks[dependency]
                )
            elif dependency in active:
                lowlinks[node] = min(
                    lowlinks[node], indices[dependency]
                )

        if lowlinks[node] != indices[node]:
            return

        component = []
        while True:
            member = stack.pop()
            active.remove(member)
            component.append(member)
            if member == node:
                break

        components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)

    owner = {
        name: index
        for index, members in enumerate(components)
        for name in members
    }

    links = {index: set() for index in range(len(components))}
    for node in nodes:
        for dependency in adjacency[node]:
            source = owner[node]
            target = owner[dependency]
            if source != target:
                links[source].add(target)

    result = []
    seen = set()

    def order(component):
        """Visit dependency groups before their dependents."""
        if component in seen:
            return

        seen.add(component)
        for dependency in sorted(
            links[component], key=lambda item: components[item]
        ):
            order(dependency)

        result.append(components[component])

    for component in sorted(links, key=lambda item: components[item]):
        order(component)

    return result
