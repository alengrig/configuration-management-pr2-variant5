"""Tests for reading Ubuntu package repository metadata."""

import gzip
import lzma
import unittest
from unittest.mock import patch
from urllib.error import URLError

from depgraph.repository import RepositoryError
from depgraph.repository import direct_dependencies, download_index
from depgraph.repository import index_url, parse_index, read_fields


SAMPLE_INDEX = (
    "Package: alpha\n"
    "Version: 1.0\n"
    "Pre-Depends: libc6 (>= 2.38)\n"
    "Depends: beta (>= 2), gamma | delta\n"
    "\n"
    "Package: beta\n"
    "Version: 2.0\n"
)


class RepositoryTests(unittest.TestCase):
    """Check parsing, downloads, and failure cases."""

    def _fake_download(self, content, address):
        """Mock network access and return the decoded metadata."""
        with patch("depgraph.repository.urlopen") as request:
            response = request.return_value.__enter__.return_value
            response.read.return_value = content
            result = download_index(address)
            request.assert_called_once_with(address, timeout=30)
        return result

    def test_archive_root_address(self):
        """Build the Ubuntu Packages index URL from a root."""
        result = index_url("https://archive.ubuntu.com/ubuntu")
        self.assertIn("/dists/noble/main/binary-amd64/", result)
        self.assertTrue(result.endswith("Packages.xz"))

    def test_exact_index_address(self):
        """Keep an explicitly provided index URL unchanged."""
        address = "https://example.org/Packages.gz"
        self.assertEqual(index_url(address), address)

    def test_multiline_control_field(self):
        """Merge an indented continuation with its preceding field."""
        fields = read_fields(["Package: alpha", "Depends: beta,", " gamma"])
        self.assertEqual(fields["depends"], "beta, gamma")

    def test_parse_multiple_packages(self):
        """Find different package records in one index."""
        packages = parse_index(SAMPLE_INDEX)
        self.assertEqual(packages["alpha"]["version"], "1.0")
        self.assertEqual(packages["beta"]["version"], "2.0")

    def test_empty_index(self):
        """Reject an index containing no packages."""
        with self.assertRaises(RepositoryError):
            parse_index("\n\n")

    def test_missing_package_field(self):
        """Reject a record without a Package field."""
        with self.assertRaises(RepositoryError):
            parse_index("Version: 1.0\n")

    def test_invalid_control_field(self):
        """Reject a line that does not contain a colon."""
        with self.assertRaises(RepositoryError):
            parse_index("Package: alpha\ninvalid-line\n")

    def test_invalid_continuation(self):
        """Reject a continuation without a previous field."""
        with self.assertRaises(RepositoryError):
            parse_index(" continuation\nPackage: alpha\n")

    def test_direct_dependencies(self):
        """Read both direct dependency fields and keep alternatives."""
        packages = parse_index(SAMPLE_INDEX)
        result = direct_dependencies(packages, "alpha")
        self.assertEqual(result, [
            ("Pre-Depends", "libc6 (>= 2.38)"),
            ("Depends", "beta (>= 2)"),
            ("Depends", "gamma | delta"),
        ])

    def test_without_dependencies(self):
        """Return an empty list for a standalone package."""
        packages = parse_index(SAMPLE_INDEX)
        self.assertEqual(direct_dependencies(packages, "beta"), [])

    def test_missing_requested_package(self):
        """Report a missing package by name."""
        with self.assertRaisesRegex(RepositoryError, "package not found"):
            direct_dependencies(parse_index(SAMPLE_INDEX), "missing")

    def test_download_xz(self):
        """Decompress xz package metadata."""
        address = "https://example.org/Packages.xz"
        self.assertEqual(
            self._fake_download(lzma.compress(SAMPLE_INDEX.encode()), address),
            SAMPLE_INDEX,
        )

    def test_download_gzip(self):
        """Decompress gzip package metadata."""
        address = "https://example.org/Packages.gz"
        self.assertEqual(
            self._fake_download(gzip.compress(SAMPLE_INDEX.encode()), address),
            SAMPLE_INDEX,
        )

    def test_download_plain(self):
        """Read an uncompressed Packages index."""
        address = "https://example.org/Packages"
        self.assertEqual(
            self._fake_download(SAMPLE_INDEX.encode(), address),
            SAMPLE_INDEX,
        )

    def test_network_error(self):
        """Convert connection errors into repository errors."""
        with patch("depgraph.repository.urlopen") as request:
            request.side_effect = URLError("offline")
            with self.assertRaisesRegex(RepositoryError, "cannot load"):
                download_index("https://example.org/Packages")

    def test_corrupted_xz(self):
        """Report invalid xz compressed data."""
        with patch("depgraph.repository.urlopen") as request:
            response = request.return_value.__enter__.return_value
            response.read.return_value = b"invalid compressed data"
            with self.assertRaises(RepositoryError):
                download_index("https://example.org/Packages.xz")

    def test_invalid_utf8(self):
        """Reject metadata that cannot be decoded as UTF-8."""
        with patch("depgraph.repository.urlopen") as request:
            response = request.return_value.__enter__.return_value
            response.read.return_value = b"\xff"
            with self.assertRaisesRegex(RepositoryError, "not UTF-8"):
                download_index("https://example.org/Packages")


if __name__ == "__main__":
    unittest.main()
