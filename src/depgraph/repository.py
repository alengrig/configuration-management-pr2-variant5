"""Read Ubuntu Packages indexes without a package manager."""

import gzip
import lzma
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


INDEX_PATH = "dists/noble/main/binary-amd64/Packages.xz"


class RepositoryError(Exception):
    """Report invalid or unavailable package metadata."""


def index_url(repository):
    """Accept an index URL or an Ubuntu archive root."""
    path = urlsplit(repository).path.lower()

    if path.endswith(("/packages", "/packages.gz", "/packages.xz")):
        return repository

    return f"{repository.rstrip('/')}/{INDEX_PATH}"


def download_index(repository):
    """Download and decode an Ubuntu package index."""
    address = index_url(repository)

    try:
        with urlopen(address, timeout=30) as response:
            content = response.read()

        if address.lower().endswith(".xz"):
            content = lzma.decompress(content)
        elif address.lower().endswith(".gz"):
            content = gzip.decompress(content)

        return content.decode("utf-8")

    except UnicodeError as error:
        raise RepositoryError("index is not UTF-8 text") from error

    except (OSError, URLError, ValueError, lzma.LZMAError) as error:
        raise RepositoryError(f"cannot load index: {error}") from error


def read_fields(lines):
    """Parse one Debian control stanza, including folded values."""
    result = {}
    previous = None

    for line in lines:
        if line.startswith((" ", "\t")):
            if previous is None:
                raise RepositoryError("invalid continuation line")
            result[previous] += " " + line.strip()
            continue

        if ":" not in line:
            raise RepositoryError("invalid control field")

        key, value = line.split(":", 1)
        previous = key.lower()
        result[previous] = value.strip()

    return result


def parse_index(text):
    """Build a lookup of package names and dependency metadata."""
    packages = {}
    lines = []

    for line in text.replace("\r\n", "\n").splitlines() + [""]:
        if line.strip():
            lines.append(line)
            continue

        if not lines:
            continue

        fields = read_fields(lines)

        if "package" not in fields:
            raise RepositoryError("Package field is missing")

        packages[fields["package"]] = fields
        lines = []

    if not packages:
        raise RepositoryError("package index is empty")

    return packages


def direct_dependencies(packages, name):
    """Return direct dependencies grouped by their metadata field."""
    if name not in packages:
        raise RepositoryError(f"package not found: {name}")

    result = []

    for field in ("pre-depends", "depends"):
        value = packages[name].get(field, "")
        label = "Pre-Depends" if field == "pre-depends" else "Depends"

        for item in value.split(","):
            dependency = item.strip()

            if dependency:
                result.append((label, dependency))

    return result
