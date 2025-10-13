import re
import subprocess
import os
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, quote_plus, unquote # Added quote_plus, unquote
from typing import Optional
from packaging.version import parse as parse_version, InvalidVersion

import requests
import sys

from ..cli_logger import logger


def get_source_package_name(package_name: str) -> str:
    return package_name


class TarballLinkFinder(HTMLParser):
    def __init__(self, package_name: str):
        super().__init__()
        self.links = []
        self.package_name = package_name # Corrected from 'package'
        source_package_name = get_source_package_name(package_name)
        self.search_names = [package_name]
        if source_package_name != package_name:
            self.search_names.append(source_package_name)
        self.version_regex = re.compile(r'(?:[a-zA-Z0-9\.-]+-)?(\d+\.\d+(?:\.\d+)*(?:-[a-zA-Z0-9\.-]+)?)(?=\.tar)')

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    if re.search(r"\.tar\.(gz|xz|bz2)$", value):
                        filename = os.path.basename(urlparse(value).path)
                        if any(filename.startswith(sn) for sn in self.search_names):
                            match = self.version_regex.search(filename)
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
        self.version_regex = re.compile(r"^(v?(\d+(?:\.\d+)*(?:(?:a|b|rc)\d+)?))/?$")

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    match = self.version_regex.search(value)
                    if match:
                        self.links.append((match.group(1), match.group(2))) # (full_link, version_str)



def find_tarball(url: str, package_name: str, version: Optional[str] = None, visited: set = None, depth: int = 0) -> Optional[str]:

    MAX_DEPTH = 3 # Limit recursion depth

    if visited is None:
        visited = set()

    if url in visited or depth > MAX_DEPTH:
        return None
    visited.add(url)

    try:
        response = requests.get(url)
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
                            return urljoin(url, link)
                        return link
            else:
                # Separate pre-releases and stable releases
                stable_releases = []
                prereleases = []
                for link, version_str in tarball_parser.links:
                    try:
                        v = parse_version(version_str)
                    except InvalidVersion as e:
                        logger.error(f"Failed to parse version '{version_str}' from link '{link}': {e}")
                        continue # Skip this link and try the next one
                    
                    if v.is_prerelease:
                        prereleases.append((link, v))
                    else:
                        stable_releases.append((link, v))

                # Prefer stable releases
                if stable_releases:
                    sorted_links = sorted(stable_releases, key=lambda x: x[1], reverse=True)
                else:
                    # If no stable releases, avoid pre-releases as requested.
                    sorted_links = []
                    logger.info(f"No stable releases found for {package_name}. Avoiding pre-releases.")

                if sorted_links:
                    link, _ = sorted_links[0]
                    if not link.startswith("http"):
                        return urljoin(url, link)
                    return link

        # If no tarball is found, look for version directories and recurse into the latest one
        version_parser = VersionLinkFinder()
        version_parser.feed(html)
        if version_parser.links:
            # Sort versions and pick the latest one
            sorted_links = sorted(version_parser.links, key=lambda x: parse_version(x[1]), reverse=True)
            if sorted_links:
                latest_version_link, _ = sorted_links[0]
                next_url = urljoin(url, latest_version_link)
                tarball_url = find_tarball(next_url, package_name, version, visited, depth + 1)
                if tarball_url:
                    return tarball_url

        # If no tarball is found, look for a source page link and recurse
        source_parser = SourcePageLinkFinder()
        source_parser.feed(html)
        for source_page_url in source_parser.links:
            if not source_page_url.startswith("http"):
                source_page_url = urljoin(url, source_page_url)
            
            tarball_url = find_tarball(source_page_url, package_name, version, visited, depth + 1) # Increment depth
            if tarball_url:
                return tarball_url

    except Exception as e:
        logger.error(f"[!] Failed to scrape tarball link from {url}: {type(e).__name__}: {e}")
    return None


def resolve_package_url(package_name: str, version: Optional[str] = None) -> Optional[str]:
    search_query = f"{package_name} download source tar.gz"
    logger.info(f"Searching for '{search_query}' using Web Search...")
    search_results = default_api.google_web_search(query=search_query)
    
    # Extract URLs from search results
    urls = []
    # Regex to find URLs in the format: (https://actual.url.com/)
    url_pattern = re.compile(r'\(https?://[^\s\)]+\)')
    for line in search_results['output'].splitlines():
        matches = url_pattern.findall(line)
        for match in matches:
            urls.append(match.strip('()'))

    if not urls:
        logger.warning(f"No URLs found in search results for '{package_name}'.")
        return None

    logger.info(f"Found {len(urls)} potential URLs. Attempting to find tarball...")
    for url in urls:
        logger.info(f"Checking URL: {url}")
        tarball_url = find_tarball(url, package_name, version)
        if tarball_url:
            logger.info(f"Found tarball for {package_name} at: {tarball_url}")
            return tarball_url

    logger.warning(f"Could not find tarball for {package_name} (version: {version or 'latest'}) after checking all search results.")
    return None
