import requests
import click
from html.parser import HTMLParser

class PyPISearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_package_snippet = False
        self.in_package_name = False
        self.in_package_description = False
        self.packages = []
        self.current_package = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'package-snippet' in attrs.get('class', ''):
            self.in_package_snippet = True
            self.current_package = {}
        if self.in_package_snippet and tag == 'span' and 'package-snippet__name' in attrs.get('class', ''):
            self.in_package_name = True
        if self.in_package_snippet and tag == 'p' and 'package-snippet__description' in attrs.get('class', ''):
            self.in_package_description = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.in_package_snippet:
            self.in_package_snippet = False
            self.packages.append(self.current_package)
            self.current_package = {}
        if tag == 'span' and self.in_package_name:
            self.in_package_name = False
        if tag == 'p' and self.in_package_description:
            self.in_package_description = False

    def handle_data(self, data):
        if self.in_package_name:
            self.current_package['name'] = data.strip()
        if self.in_package_description:
            self.current_package['description'] = data.strip()

@click.command()
@click.argument('package_name')
def search_packages(package_name):
    """Search for packages on PyPI."""
    url = f"https://pypi.org/search/?q={package_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    parser = PyPISearchParser()
    parser.feed(resp.text)

    if parser.packages:
        for package in parser.packages:
            if 'name' in package and 'description' in package:
                click.echo(f"{package['name']} - {package['description']}")
    else:
        click.echo(f"No packages found for '{package_name}'.")
