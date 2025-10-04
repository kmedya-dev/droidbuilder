import requests
from urllib.parse import quote_plus, unquote
import click
from html.parser import HTMLParser

class DuckDuckGoSearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found_links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value.startswith('//duckduckgo.com/l/?uddg='):
                    # Extract the actual URL from the uddg parameter
                    start_index = value.find('uddg=') + len('uddg=')
                    end_index = value.find('&', start_index)
                    if end_index == -1:
                        end_index = len(value)
                    encoded_url = value[start_index:end_index]
                    decoded_url = unquote(encoded_url)
                    self.found_links.append(decoded_url)

@click.command()
@click.argument('package_name')
@click.argument('version', required=False, default="latest")
def search(package_name, version):
    query = f"{package_name} {version} official source tarball download link"
    encoded = quote_plus(query)
    url = f"https://duckduckgo.com/html/?q={encoded}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    parser = DuckDuckGoSearchParser()
    parser.feed(resp.text)

    if parser.found_links:
        for link in parser.found_links:
            click.echo(link)
    else:
        click.echo(f"No download links found for {package_name} {version}.")