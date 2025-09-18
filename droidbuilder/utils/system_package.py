import json
import os
import re
import subprocess
import tomllib  # Python 3.11+
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from ..cli_logger import logger


class TarballLinkFinder(HTMLParser):
    def __init__(self, package_name: str):
        super().__init__()
        self.links = []
        self.package_name = package_name

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and re.search(r"\.tar\.(gz|xz|bz2)$", value):
                    # Prioritize links that contain the package name
                    if self.package_name in value:
                        self.links.insert(0, value)
                    else:
                        self.links.append(value)

class SourcePageLinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    if "source" in value.lower() or "download" in value.lower() or "library" in value.lower() or "releases" in value.lower():
                        self.links.append(value)


def find_tarball(homepage: str, package_name: str, visited: set = None) -> str | None:
    if visited is None:
        visited = set()

    if homepage in visited:
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
            link = tarball_parser.links[0]
            if not link.startswith("http"):
                return urljoin(homepage, link)
            return link

        # If no tarball is found, look for a source page link and recurse
        source_parser = SourcePageLinkFinder()
        source_parser.feed(html)
        for source_page_url in source_parser.links:
            if not source_page_url.startswith("http"):
                source_page_url = urljoin(homepage, source_page_url)
            
            tarball_url = find_tarball(source_page_url, package_name, visited)
            if tarball_url:
                return tarball_url

    except Exception as e:
        logger.error(f"[!] Failed to scrape tarball link from {homepage}: {e}")
    return None


def resolve_system_package(package_name: str) -> str | None:
    """
    Resolves the homepage for a system package using apt.
    """
    try:
        # Try apt show first
        process = subprocess.run(
            ['apt', 'show', package_name],
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

        # If not found, search candidates
        search_process = subprocess.run(
            ['apt', 'search', package_name],
            capture_output=True,
            text=True,
            check=False
        )
        if search_process.returncode == 0:
            for line in search_process.stdout.splitlines():
                match = re.match(r"^([a-z0-9.+-]+)\/", line)
                if match:
                    real_pkg = match.group(1)
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
                        continue
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
                tarball_url = find_tarball(homepage, name)
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