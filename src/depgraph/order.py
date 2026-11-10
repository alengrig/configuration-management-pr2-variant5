"""Determine dependency-first installation groups."""


def _build_adjacency(graph):
    """Include every node, even if it has no own graph entry."""
    nodes = set(graph)

    for dependencies in graph.values():
        nodes.update(dependencies)

    return {
        node: sorted(set(graph.get(node, [])))
        for node in nodes
    }


class _ComponentFinder:
    """Find strongly connected components with Tarjan's algorithm."""

    def __init__(self, adjacency):
        self.adjacency = adjacency
        self.indices = {}
        self.lowlinks = {}
        self.stack = []
        self.active = set()
        self.components = []
        self.next_index = 0

    def _inspect_dependency(self, node, dependency):
        """Update lowlink values for a dependency."""
        if dependency not in self.indices:
            self._visit(dependency)
            self.lowlinks[node] = min(
                self.lowlinks[node],
                self.lowlinks[dependency],
            )
        elif dependency in self.active:
            self.lowlinks[node] = min(
                self.lowlinks[node],
                self.indices[dependency],
            )

    def _pop_component(self, node):
        """Remove a completed component from the stack."""
        component = []

        while True:
            member = self.stack.pop()
            self.active.remove(member)
            component.append(member)

            if member == node:
                break

        self.components.append(sorted(component))

    def _visit(self, node):
        """Visit a node using Tarjan's depth-first search."""
        self.indices[node] = self.next_index
        self.lowlinks[node] = self.next_index
        self.next_index += 1

        self.stack.append(node)
        self.active.add(node)

        for dependency in self.adjacency[node]:
            self._inspect_dependency(node, dependency)

        if self.lowlinks[node] == self.indices[node]:
            self._pop_component(node)

    def find_components(self):
        """Find all strongly connected components."""
        for node in sorted(self.adjacency):
            if node not in self.indices:
                self._visit(node)

        return self.components


def _component_links(adjacency, components):
    """Build dependencies between components."""
    owner = {
        name: index
        for index, members in enumerate(components)
        for name in members
    }

    links = {
        index: set()
        for index in range(len(components))
    }

    for node, dependencies in adjacency.items():
        for dependency in dependencies:
            source = owner[node]
            target = owner[dependency]

            if source != target:
                links[source].add(target)

    return links


def _order_components(components, links):
    """Return groups in dependency-first order."""
    result = []
    seen = set()

    def visit(component):
        if component in seen:
            return

        seen.add(component)

        for dependency in sorted(
            links[component],
            key=lambda item: components[item],
        ):
            visit(dependency)

        result.append(components[component])

    for component in sorted(
        links,
        key=lambda item: components[item],
    ):
        visit(component)

    return result


def installation_groups(graph):
    """Order dependencies first and keep cycles together."""
    adjacency = _build_adjacency(graph)
    components = _ComponentFinder(adjacency).find_components()
    links = _component_links(adjacency, components)

    return _order_components(components, links)