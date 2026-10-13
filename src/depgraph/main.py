"""Command-line entry point for Ubuntu dependency analysis."""

import sys
from pathlib import Path
from depgraph.graph import GraphError, build_graph, build_providers
from depgraph.graph import ubuntu_dependencies
from depgraph.graph import parse_test_repository

from depgraph.config import parse_arguments, print_configuration
from depgraph.repository import RepositoryError
from depgraph.repository import direct_dependencies
from depgraph.repository import download_index, parse_index


def show_dependencies(config):
    """Display direct dependencies of an Ubuntu package."""
    metadata = download_index(config.repository)
    packages = parse_index(metadata)
    providers = build_providers(packages)
    dependencies = direct_dependencies(packages, config.package)

    print(f"Package: {config.package}")
    print(f"Version: {packages[config.package].get('version', 'unknown')}")
    print("Direct dependencies:")

    if not dependencies:
        print("  (none)")

    for label, dependency in dependencies:
        print(f"  {label}: {dependency}")

    graph, cycles = build_graph(
        config.package,
        lambda name: ubuntu_dependencies(packages, name, providers)[0],
    )

    unresolved = []
    for name in graph:
        _, missing = ubuntu_dependencies(packages, name, providers)
        for requirement in missing:
            unresolved.append((name, requirement))

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


def main(arguments=None):
    """Run the dependency analysis application."""
    config = parse_arguments(arguments)
    print_configuration(config)

    if config.test_mode:
        try:
            text = Path(config.repository).read_text(encoding="utf-8")
            repository = parse_test_repository(text)

            if config.package not in repository:
                raise GraphError(f"package not found: {config.package}")

            graph, cycles = build_graph(
                config.package, repository.__getitem__
            )
        except (OSError, GraphError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        print("Dependency graph:")
        for package, children in graph.items():
            print(f"{package}: {' '.join(children)}")

        print("Cycles:")
        if cycles:
            for cycle in cycles:
                print(" -> ".join(cycle))
        else:
            print("none")

        return 0

    try:
        show_dependencies(config)
    except RepositoryError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
