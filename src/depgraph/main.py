"""Main entry point for the dependency graph application."""

from depgraph.config import parse_arguments
from depgraph.config import print_configuration


def main(arguments=None):
    """Run the command-line application."""
    config = parse_arguments(arguments)
    print_configuration(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
