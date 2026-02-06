#!/usr/bin/env python3
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


def load_env():
    # Read NetBox connection details from .env.
    load_dotenv(".env")
    url = os.getenv("NETBOX_URL")
    token = os.getenv("NETBOX_TOKEN")
    if not url or not token:
        raise RuntimeError("Missing NETBOX_URL or NETBOX_TOKEN in .env")
    return url.rstrip("/"), token


def fetch_json(url, token):
    # GET a URL and return JSON.
    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def build_examples(apps):
    # Build markdown content from API root structure.
    lines = [
        "# Examples",
        "",
        "This file provides example commands for working with the local `nbcli` script and",
        "the target NetBox API.",
        "",
        "## Local script examples",
        "",
        "Run the root script:",
        "",
        "```",
        "./nbcli status",
        "```",
        "",
        "Show CLI configuration:",
        "",
        "```",
        "./nbcli get cli config",
        "```",
        "",
        "Select a single value from the CLI config:",
        "",
        "```",
        "./nbcli get cli config --path .timeout",
        "```",
        "",
        "List devices with filters:",
        "",
        "```",
        "./nbcli list dcim/devices --filter role=leaf --filter site=dc1",
        "```",
        "",
        "Output formats:",
        "",
        "```",
        "./nbcli get status --json",
        "./nbcli get status --yaml",
        "./nbcli get status --csv",
        "```",
        "",
        "## NetBox API examples",
        "",
        "The commands below use endpoints discovered from `/api/` on your NetBox instance.",
        "",
        "Get API status:",
        "",
        "```",
        "./nbcli get status",
        "```",
        "",
        "Select a single value from a response:",
        "",
        "```",
        "./nbcli get status --path .netbox-version",
        "./nbcli list dcim/devices --path .results.0.name",
        "```",
    ]

    for app, endpoints in sorted(apps.items()):
        title = app.replace("-", " ").replace("_", " ").title()
        lines.extend(
            [
                "",
                f"## {title} objects",
                "",
                "```",
            ]
        )
        for endpoint in endpoints:
            lines.append(f"./nbcli list {app}/{endpoint}")
        lines.extend(["```"])
    return "\n".join(lines) + "\n"


def main():
    base_url, token = load_env()
    root = fetch_json(f"{base_url}/api/", token)
    apps = {}
    for app, url in root.items():
        if app == "status":
            continue
        payload = fetch_json(url, token)
        apps[app] = sorted(payload.keys())

    content = build_examples(apps)
    output_path = Path("examples.md")
    output_path.write_text(content)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
