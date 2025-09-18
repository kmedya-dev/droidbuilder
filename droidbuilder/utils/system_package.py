import json
import os
import re
import subprocess
import tomllib  # Python 3.11+
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from packaging.version import parse as parse_version

import requests

from ..cli_logger import logger


class TarballLinkFinder(HTMLParser):
    def __init__(self, package_name: str):
        super().__init__()
        self.links = []
        self.package_name = package_name
        self.search_names = [package_name]
        if package_name == 'libssl-dev':
            self.search_names.append('openssl')
        self.version_regex = re.compile(r'(\d+\.\d+(?:\.\d+)*(?:-[a-zA-Z0-9\.-]+)?)(?=\.tar)')

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and re.search(r"\.tar\.(gz|xz|bz2)$", value):
                    if any(sn in value for sn in self.search_names):
                        match = self.version_regex.search(value)
                        if match:
                            self.links.append((value, match.group(1)))

class SourcePageLinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.priority_keywords = ["releases", "download", "archive"]
        self.general_keywords = ["source", "library", "files", "dist", "get"]

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    lower_value = value.lower()
                    if any(keyword in lower_value for keyword in self.priority_keywords):
                        self.links.insert(0, value)
                    elif any(keyword in lower_value for keyword in self.general_keywords):
                        self.links.append(value)

class VersionLinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        # Regex to find version numbers in format vX.Y.Z or X.Y.Z
        self.version_regex = re.compile(r"(v?(\d+\.\d+(?:\.\d+)*?(?:-[a-zA-Z0-9\.-]+)?)/?)$")

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    match = self.version_regex.search(value)
                    if match:
                        self.links.append((match.group(1), match.group(2))) # (full_link, version_str)


def find_tarball(homepage: str, package_name: str, version: str | None = None, visited: set = None, depth: int = 0) -> str | None:
    # HACK: for uuid-dev, the package is util-linux
    if package_name == 'uuid-dev':
        package_name = 'util-linux'

    MAX_DEPTH = 2 # Limit recursion depth

    if visited is None:
        visited = set()

    if homepage in visited or depth > MAX_DEPTH:
        return None
    visited.add(homepage)

    # Special handling for GitHub
    if 'github.com' in homepage:
        # If it's a GitHub release tag page, construct the tarball URL
        match = re.search(r'github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/releases/tag/(?P<tag>[^/]+)', homepage)
        if match:
            owner = match.group('owner')
            repo = match.group('repo')
            tag = match.group('tag')
            tarball_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag}.tar.gz"
            return tarball_url

        if '/releases' not in homepage and '/archive' not in homepage: # Also check for archive
            homepage = urljoin(homepage, 'releases')
            if homepage in visited or depth > MAX_DEPTH: # Re-check after modifying homepage
                return None
            visited.add(homepage)

    try:
        response = requests.get(homepage)
        response.raise_for_status()
        html = response.text

        # Look for a tarball on the current page
        tarball_parser = TarballLinkFinder(package_name)
        tarball_parser.feed(html)
        
        if tarball_parser.links:
            if version:
                for link, version_str in tarball_parser.links:
                    if version_str == version:
                        if not link.startswith("http"):
                            return urljoin(homepage, link)
                        return link
            else:
                # Separate pre-releases and stable releases
                stable_releases = []
                prereleases = []
                for link, version_str in tarball_parser.links:
                    v = parse_version(version_str)
                    if v.is_prerelease:
                        prereleases.append((link, v))
                    else:
                        stable_releases.append((link, v))

                # Prefer stable releases
                if stable_releases:
                    sorted_links = sorted(stable_releases, key=lambda x: x[1], reverse=True)
                else:
                    sorted_links = sorted(prereleases, key=lambda x: x[1], reverse=True)

                if sorted_links:
                    link, _ = sorted_links[0]
                    if not link.startswith("http"):
                        return urljoin(homepage, link)
                    return link

        # If no tarball is found, look for version directories and recurse into the latest one
        version_parser = VersionLinkFinder()
        version_parser.feed(html)
        if version_parser.links:
            # Sort versions and pick the latest one
            sorted_links = sorted(version_parser.links, key=lambda x: parse_version(x[1]), reverse=True)
            if sorted_links:
                latest_version_link, _ = sorted_links[0]
                next_url = urljoin(homepage, latest_version_link)
                tarball_url = find_tarball(next_url, package_name, version, visited, depth + 1)
                if tarball_url:
                    return tarball_url

        # If no tarball is found, look for a source page link and recurse
        source_parser = SourcePageLinkFinder()
        source_parser.feed(html)
        for source_page_url in source_parser.links:
            if not source_page_url.startswith("http"):
                source_page_url = urljoin(homepage, source_page_url)
            
            tarball_url = find_tarball(source_page_url, package_name, version, visited, depth + 1) # Increment depth
            if tarball_url:
                return tarball_url

    except Exception as e:
        logger.error(f"[!] Failed to scrape tarball link from {homepage}: {e}")
    return None


def resolve_system_package(package_name: str) -> str | None:
    """
    Resolves the homepage for a system package using apt.
    Includes a heuristic to filter out potentially unofficial homepages.
    """
    package_names_to_try = []
    if not package_name.startswith('lib') and not package_name.endswith('-dev'):
        package_names_to_try.append(f"lib{package_name}-dev")
        package_names_to_try.append(f"lib{package_name}")
    package_names_to_try.append(f"{package_name}-dev")
    package_names_to_try.append(package_name)

    for pkg_name in package_names_to_try:
        try:
            # Try apt show first
            process = subprocess.run(
                ['apt', 'show', pkg_name],
                capture_output=True,
                text=True,
                check=False
            )
            if process.returncode == 0:
                for line in process.stdout.splitlines():
                    if line.lower().startswith('homepage:'):
                        url = line.split(':', 1)[1].strip()
                        if url:  # Ensure URL is not empty
                            return url
        except FileNotFoundError:
            logger.error("apt command not found. Cannot resolve system package.")
            return None

    # If not found, search candidates
    try:
        search_process = subprocess.run(
            ['apt', 'search', package_name],
            capture_output=True,
            text=True,
            check=False
        )
        if search_process.returncode == 0:
            candidates = []
            for line in search_process.stdout.splitlines():
                match = re.match(r"^([a-z0-9.+-]+)\/", line)
                if match:
                    candidates.append(match.group(1))
            
            prioritized_candidates = []
            
            # Add exact matches first
            if f"lib{package_name}-dev" in candidates:
                prioritized_candidates.append(f"lib{package_name}-dev")
            if f"lib{package_name}" in candidates:
                prioritized_candidates.append(f"lib{package_name}")
            if f"{package_name}-dev" in candidates:
                prioritized_candidates.append(f"{package_name}-dev")
            if package_name in candidates:
                prioritized_candidates.append(package_name)
            
            # Add other candidates that contain the package name
            for c in candidates:
                if c not in prioritized_candidates and package_name in c:
                    prioritized_candidates.append(c)
            
            for real_pkg in prioritized_candidates:
                try:
                    show_process = subprocess.run(
                        ['apt', 'show', real_pkg],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if show_process.returncode == 0:
                        for l in show_process.stdout.splitlines():
                            if l.lower().startswith("homepage:"):
                                url = l.split(":", 1)[1].strip()
                                if url:  # Ensure URL is not empty
                                    return url
                except subprocess.CalledProcessError:
                    pass # Continue to next candidate if apt show fails
    except FileNotFoundError:
        logger.error("apt command not found. Cannot resolve system package.")
        return None

    logger.warning(f"⚠️ No homepage found for {package_name}. Consider adding URL mapping.")
    return None


def resolve_dependencies_recursively(packages, dependency_mapping):
    """
    Resolves system packages against the dependency mapping.
    If a package is not in the mapping, it attempts to find the URL.
    Returns a dictionary mapping package names to their URLs.
    """
    resolved_packages = {}

    for package_spec in packages:
        if '==' in package_spec:
            name, version = package_spec.split('==', 1)
        else:
            name, version = package_spec, None

        if name in resolved_packages:
            continue

        if name in dependency_mapping and dependency_mapping[name]:
            resolved_packages[name] = dependency_mapping[name]
            logger.info(f"Found mapping for '{name}': {dependency_mapping[name]}")
        else:
            logger.warning(f"System package '{name}' is not explicitly mapped in your droidbuilder.toml.")
            logger.info(f"Attempting to resolve '{name}' automatically...")
            homepage = resolve_system_package(name)
            if homepage:
                logger.info(f"Found homepage for '{name}': {homepage}")
                tarball_url = find_tarball(homepage, name, version=version)
                if tarball_url:
                    logger.success(f"Found tarball for '{name}': {tarball_url}")
                    resolved_packages[name] = tarball_url
                else:
                    logger.error(f"Could not find a downloadable tarball for '{name}' from its homepage.")
                    logger.error("Please add its URL to [project.requirements.dependency_mapping]")
                    return None
            else:
                logger.error(f"Could not find a homepage for '{name}'.")
                logger.error("Please add its URL to [project.requirements.dependency_mapping]")
                return None

    return resolved_packages
