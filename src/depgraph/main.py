"""Command-line entry point for Ubuntu dependency analysis."""

import sys
from pathlib import Path

from depgraph.config import parse_arguments, print_configuration
from depgraph.graph import (
    GraphError,
    build_graph,
    build_providers,
    parse_test_repository,
    ubuntu_dependencies,
)
from depgraph.order import installation_groups
from depgraph.repository import (
    RepositoryError,
    direct_dependencies,
    download_index,
    parse_index,
)
from depgraph.visualize import render_graph


def print_installation_order(graph):
    """Print dependency groups in dependency-first order."""
    groups = installation_groups(graph)
    print("Dependency-first installation groups:")

    for number, members in enumerate(groups, start=1):
        print(f"  {number}. {', '.join(members)}")


def print_direct_dependencies(package, packages, dependencies):
    """Print package information and immediate dependencies."""
    print(f"Package: {package}")
    print(f"Version: {packages[package].get('version', 'unknown')}")
    print("Direct dependencies:")

    if not dependencies:
        print("  (none)")

    for label, dependency in dependencies:
        print(f"  {label}: {dependency}")


def find_unresolved(graph, packages, providers):
    """Collect unresolved dependency groups."""
    unresolved = []

    for name in graph:
        _, missing = ubuntu_dependencies(packages, name, providers)

        for requirement in missing:
            unresolved.append((name, requirement))

    return unresolved


def print_transitive_dependencies(graph, cycles, unresolved):
    """Display graph, cycles and unresolved dependencies."""
    print("Transitive dependency graph:")

    for name, children in graph.items():
        value = ", ".join(children) if children else "(none)"
        print(f"  {name}: {value}")

    print(f"Packages in graph: {len(graph)}")
    print(f"Cycles found: {len(cycles)}")

    for cycle in cycles:
        print("  " + " -> ".join(cycle))

    print(f"Unresolved dependency groups: {len(unresolved)}")

    for name, requirement in unresolved:
        print(f"  {name}: {requirement}")


def save_graph(graph, output):
    """Print installation order and save PNG."""
    print_installation_order(graph)
    render_graph(graph, output)
    print(f"PNG created: {output}")


def show_dependencies(config):
    """Analyze and display Ubuntu package dependencies."""
    metadata = download_index(config.repository)
    packages = parse_index(metadata)
    providers = build_providers(packages)

    dependencies = direct_dependencies(packages, config.package)
    print_direct_dependencies(config.package, packages, dependencies)

    graph, cycles = build_graph(
        config.package,
        lambda name: ubuntu_dependencies(packages, name, providers)[0],
    )

    unresolved = find_unresolved(graph, packages, providers)
    print_transitive_dependencies(graph, cycles, unresolved)
    save_graph(graph, config.output)


def load_test_graph(config):
    """Load and build a graph from a test repository."""
    text = Path(config.repository).read_text(encoding="utf-8")
    repository = parse_test_repository(text)

    if config.package not in repository:
        raise GraphError(f"package not found: {config.package}")

    return build_graph(config.package, repository.__getitem__)


def print_test_graph(graph, cycles):
    """Display graph and cycles in test mode."""
    print("Dependency graph:")

    for package, children in graph.items():
        print(f"{package}: {' '.join(children)}")

    print("Cycles:")

    if cycles:
        for cycle in cycles:
            print(" -> ".join(cycle))
    else:
        print("none")


def run_test_mode(config):
    """Run dependency analysis using a test repository."""
    try:
        graph, cycles = load_test_graph(config)
    except (OSError, GraphError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print_test_graph(graph, cycles)
    save_graph(graph, config.output)
    return 0


def main(arguments=None):
    """Run the dependency analysis application."""
    config = parse_arguments(arguments)
    print_configuration(config)

    if config.test_mode:
        return run_test_mode(config)

    try:
        show_dependencies(config)
    except RepositoryError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())