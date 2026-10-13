"""Tests for the command-line configuration."""

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from depgraph.config import parse_arguments, print_configuration


REPOSITORY_URL = "https://archive.ubuntu.com/ubuntu"


class ConfigTests(unittest.TestCase):
    """Verify configuration parsing and validation."""

    def _valid_arguments(self):
        """Return valid arguments for normal mode."""
        return [
            "--package", "bash",
            "--repository", REPOSITORY_URL,
            "--output", "output/graph.png",
        ]

    def _expect_error(self, arguments):
        """Check that invalid arguments cause an error."""
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as result:
                parse_arguments(arguments)

        self.assertNotEqual(result.exception.code, 0)

    def test_real_repository_settings(self):
        """Accept normal repository settings."""
        config = parse_arguments(self._valid_arguments())
        self.assertEqual(config.package, "bash")
        self.assertFalse(config.test_mode)

    def test_test_repository_settings(self):
        """Accept test repository settings."""
        config = parse_arguments([
            "--package", "A",
            "--repository", "examples/repositories/simple.txt",
            "--test-mode",
            "--output", "output/graph.png",
        ])
        self.assertTrue(config.test_mode)
        self.assertEqual(config.package, "A")

    def test_missing_required_option(self):
        """Reject missing required parameters."""
        arguments = self._valid_arguments()[2:]
        self._expect_error(arguments)

    def test_invalid_real_package(self):
        """Reject uppercase names in normal mode."""
        arguments = self._valid_arguments()
        arguments[1] = "BASH"
        self._expect_error(arguments)

    def test_invalid_test_package(self):
        """Reject lowercase names in test mode."""
        arguments = [
            "--package", "a",
            "--repository", "examples/repositories/simple.txt",
            "--test-mode",
            "--output", "output/graph.png",
        ]
        self._expect_error(arguments)

    def test_invalid_repository_url(self):
        """Reject an invalid repository URL."""
        arguments = self._valid_arguments()
        arguments[3] = "wrong-address"
        self._expect_error(arguments)

    def test_missing_test_repository(self):
        """Reject a nonexistent test repository."""
        arguments = [
            "--package", "A",
            "--repository", "examples/repositories/missing.txt",
            "--test-mode",
            "--output", "output/graph.png",
        ]
        self._expect_error(arguments)

    def test_wrong_output_extension(self):
        """Require PNG output."""
        arguments = self._valid_arguments()
        arguments[-1] = "output/graph.svg"
        self._expect_error(arguments)

    def test_missing_output_directory(self):
        """Reject a nonexistent output directory."""
        arguments = self._valid_arguments()
        arguments[-1] = "missing_folder/graph.png"
        self._expect_error(arguments)

    def test_print_all_settings(self):
        """Print all configuration settings."""
        config = parse_arguments(self._valid_arguments())
        output = StringIO()

        with redirect_stdout(output):
            print_configuration(config)

        text = output.getvalue()
        self.assertIn("package: bash", text)
        self.assertIn("repository:", text)
        self.assertIn("test_mode: False", text)
        self.assertIn("output: output/graph.png", text)


if __name__ == "__main__":
    unittest.main()
