"""Command-line entry point for Ubuntu dependency analysis."""

import sys

from depgraph.config import parse_arguments, print_configuration
from depgraph.repository import RepositoryError
from depgraph.repository import direct_dependencies
from depgraph.repository import download_index, parse_index


def show_dependencies(config):
    """Display direct dependencies of an Ubuntu package."""
    metadata = download_index(config.repository)
    packages = parse_index(metadata)
    dependencies = direct_dependencies(packages, config.package)

    print(f"Package: {config.package}")
    print(f"Version: {packages[config.package].get('version', 'unknown')}")
    print("Direct dependencies:")

    if not dependencies:
        print("  (none)")

    for label, dependency in dependencies:
        print(f"  {label}: {dependency}")


def main(arguments=None):
    """Run the dependency analysis application."""
    config = parse_arguments(arguments)
    print_configuration(config)

    if config.test_mode:
        print("Test graph analysis will be added at stage 3.")
        return 0

    try:
        show_dependencies(config)
    except RepositoryError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
