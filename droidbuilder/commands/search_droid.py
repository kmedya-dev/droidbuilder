import requests
import click

@click.command()
@click.argument('droid_name')
def search(droid_name):
    """Search for droids on GitHub."""
    url = f"https://api.github.com/search/repositories?q=topic:droid+{droid_name}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    data = resp.json()

    if data["items"]:
        for item in data["items"]:
            click.echo(f"{item['full_name']} - {item['description']}")
    else:
        click.echo(f"No droids found for '{droid_name}'.")
