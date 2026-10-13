"""Command-line configuration for dependency analysis."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit


def build_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Ubuntu package dependency graph analyzer"
    )
    parser.add_argument("--package", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--test-mode", action="store_true")
    parser.add_argument("--output", required=True)
    return parser


def validate_package(config):
    """Validate the package name for the selected mode."""
    if config.test_mode:
        if not re.fullmatch(r"[A-Z]+", config.package):
            return "test package name must contain only A-Z"
    elif not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", config.package):
        return "Ubuntu package name must use lowercase letters"
    return None


def validate_repository(config):
    """Validate the repository URL or local test file."""
    if config.test_mode:
        if not Path(config.repository).is_file():
            return "test repository file does not exist"
        return None

    try:
        address = urlsplit(config.repository)
    except ValueError:
        return "invalid repository URL"

    if address.scheme not in {"http", "https"} or not address.netloc:
        return "repository must be an HTTP(S) URL"
    return None


def validate_output(config):
    """Validate the output PNG filename."""
    path = Path(config.output)

    if path.suffix.lower() != ".png":
        return "output filename must end with .png"

    if not path.parent.is_dir():
        return "output directory does not exist"

    if path.is_dir():
        return "output path must be a file"

    return None


def parse_arguments(arguments=None):
    """Parse and validate all command-line arguments."""
    parser = build_parser()
    config = parser.parse_args(arguments)

    checks = (
        validate_package,
        validate_repository,
        validate_output,
    )

    for check in checks:
        error = check(config)
        if error:
            parser.error(error)

    return config


def print_configuration(config):
    """Print configuration as key-value pairs."""
    print(f"package: {config.package}")
    print(f"repository: {config.repository}")
    print(f"test_mode: {config.test_mode}")
    print(f"output: {config.output}")
