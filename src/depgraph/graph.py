"""Build transitive dependency graphs with recursive DFS."""

import re


class GraphError(Exception):
    """Report an invalid test graph."""


def _parse_test_line(line, number):
    """Parse and validate one test repository line."""
    name, separator, remainder = line.partition(":")
    name = name.strip()
    dependencies = remainder.split()

    if not separator or not re.fullmatch(r"[A-Z]+", name):
        raise GraphError(f"invalid package on line {number}")

    if any(not re.fullmatch(r"[A-Z]+", item)
           for item in dependencies):
        raise GraphError(f"invalid dependency on line {number}")

    return name, dependencies


def _validate_test_graph(graph):
    """Check that the test graph is not empty or incomplete."""
    if not graph:
        raise GraphError("test repository is empty")

    referenced = {
        item
        for values in graph.values()
        for item in values
    }
    missing = referenced - graph.keys()

    if missing:
        raise GraphError(
            f"undefined packages: {', '.join(sorted(missing))}"
        )


def parse_test_repository(text):
    """Read lines like 'A: B C' into an adjacency dictionary."""
    graph = {}

    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        name, dependencies = _parse_test_line(line, number)

        if name in graph:
            raise GraphError(f"duplicate package: {name}")

        graph[name] = dependencies

    _validate_test_graph(graph)
    return graph


def build_graph(root, dependencies_for):
    """Return reachable edges and cycles found by recursive DFS."""
    result = {}
    visited = set()
    stack = []
    cycles = []

    def dfs(package):
        """Explore all dependencies of one package recursively."""
        if package in stack:
            cycles.append(stack[stack.index(package):] + [package])
            return
        if package in visited:
            return
        stack.append(package)
        children = list(dependencies_for(package))
        result[package] = children
        for child in children:
            dfs(child)
        stack.pop()
        visited.add(package)

    dfs(root)
    return result, cycles


def _requirement_alternatives(requirement):
    """Extract package names from alternative dependencies."""
    alternatives = []

    for option in requirement.split("|"):
        match = re.match(
            r"\s*([a-z0-9][a-z0-9+.-]*)", option
        )

        if match:
            alternatives.append(match.group(1))

    return alternatives


def _select_alternative(alternatives, packages, providers):
    """Select the first available package or virtual provider."""
    for item in alternatives:
        if item in packages:
            return item

        candidates = (providers or {}).get(item, [])

        if candidates:
            return candidates[0]

    return None


def ubuntu_dependencies(packages, name, providers=None):
    """Resolve direct dependencies from Ubuntu package metadata."""
    from depgraph.repository import direct_dependencies

    if name not in packages:
        return [], []

    children = []
    unresolved = []

    for _, requirement in direct_dependencies(packages, name):
        alternatives = _requirement_alternatives(requirement)
        selected = _select_alternative(
            alternatives, packages, providers
        )

        if selected is None:
            unresolved.append(requirement)
        elif selected not in children:
            children.append(selected)

    return children, unresolved


def build_providers(packages):
    """Index virtual package names declared by Provides."""
    providers = {}

    for package in sorted(packages):
        value = packages[package].get("provides", "")

        for item in value.split(","):
            match = re.match(
                r"\s*([a-z0-9][a-z0-9+.-]*)", item
            )

            if match:
                name = match.group(1)
                providers.setdefault(name, []).append(package)

    return providers