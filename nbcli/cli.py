import argparse
import os
import sys
from urllib.parse import urlsplit, urlunsplit

import requests
from dotenv import load_dotenv

from nbcli.utils.formatters import output_payload, output_status


def load_config():
    load_dotenv()
    base_url = os.getenv("NETBOX_URL")
    token = os.getenv("NETBOX_TOKEN")
    if not base_url or not token:
        print("Missing NETBOX_URL or NETBOX_TOKEN in .env", file=sys.stderr)
        sys.exit(2)
    return base_url, token


def build_url(base_url, path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = base_url.rstrip("/")
    cleaned = path.lstrip("/")
    if cleaned.startswith("api/"):
        return f"{base}/{cleaned}"
    return f"{base}/api/{cleaned}"


def ensure_trailing_slash(url):
    parts = urlsplit(url)
    path = parts.path
    if not path.endswith("/"):
        path = f"{path}/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def is_status_path(path):
    cleaned = path.strip().lstrip("/")
    if cleaned.startswith("api/"):
        cleaned = cleaned[4:]
    cleaned = cleaned.rstrip("/")
    return cleaned == "status"


def parse_kv_list(values):
    params = {}
    for item in values or []:
        if "=" not in item:
            print(f"Invalid param '{item}'. Use key=value.", file=sys.stderr)
            sys.exit(2)
        key, value = item.split("=", 1)
        if key in params:
            if isinstance(params[key], list):
                params[key].append(value)
            else:
                params[key] = [params[key], value]
        else:
            params[key] = value
    return params


def request_json(method, url, token, params, timeout, verify):
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    resp = requests.request(
        method, url, headers=headers, params=params, timeout=timeout, verify=verify
    )
    if not resp.ok:
        print(f"{resp.status_code} {resp.reason}", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        sys.exit(1)
    try:
        return resp.json()
    except ValueError:
        print(resp.text)
        sys.exit(0)


def request_all(url, token, params, timeout, verify):
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    results = []
    next_url = url
    first_params = params
    while next_url:
        resp = requests.get(
            next_url, headers=headers, params=first_params, timeout=timeout, verify=verify
        )
        first_params = None
        if not resp.ok:
            print(f"{resp.status_code} {resp.reason}", file=sys.stderr)
            print(resp.text, file=sys.stderr)
            sys.exit(1)
        payload = resp.json()
        if not isinstance(payload, dict) or "results" not in payload:
            return payload
        results.extend(payload.get("results", []))
        next_url = payload.get("next")
    return {"count": len(results), "results": results}


def main():
    parser = argparse.ArgumentParser(
        description="Interrogate a NetBox 4.4 API from the command line."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="HTTP timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification",
    )

    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--plain", action="store_true", help="Print plain text output"
    )
    format_group.add_argument(
        "--json", action="store_true", help="Print JSON output"
    )
    format_group.add_argument(
        "--yaml", action="store_true", help="Print YAML output"
    )
    format_group.add_argument("--csv", action="store_true", help="Print CSV output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Fetch /api/status/")

    get_parser = subparsers.add_parser(
        "get", help="GET an API path, e.g. dcim/devices/1"
    )
    get_parser.add_argument("path", help="API path or full URL")
    get_parser.add_argument(
        "--param",
        action="append",
        help="Query param in key=value form (repeatable)",
    )

    list_parser = subparsers.add_parser(
        "list", help="List an endpoint with optional pagination"
    )
    list_parser.add_argument("endpoint", help="API endpoint, e.g. dcim/devices")
    list_parser.add_argument(
        "--param",
        action="append",
        help="Query param in key=value form (repeatable)",
    )
    list_parser.add_argument(
        "--all",
        action="store_true",
        help="Follow pagination and return all results",
    )

    args = parser.parse_args()
    base_url, token = load_config()
    verify = not args.insecure
    params = parse_kv_list(getattr(args, "param", None))
    fmt = "pretty"
    if args.plain:
        fmt = "plain"
    elif args.json:
        fmt = "json"
    elif args.yaml:
        fmt = "yaml"
    elif args.csv:
        fmt = "csv"
    allow_color = fmt == "pretty" and sys.stdout.isatty()

    if args.command == "status":
        url = ensure_trailing_slash(build_url(base_url, "status"))
        payload = request_json("GET", url, token, None, args.timeout, verify)
        version = None
        if isinstance(payload, dict):
            version = payload.get("netbox-version") or payload.get("netbox_version")
        if version and output_status(version, fmt, allow_color):
            return
        output_payload(payload, fmt, allow_color)
        return

    if args.command == "get":
        if is_status_path(args.path):
            url = ensure_trailing_slash(build_url(base_url, "status"))
            payload = request_json("GET", url, token, None, args.timeout, verify)
            version = None
            if isinstance(payload, dict):
                version = payload.get("netbox-version") or payload.get(
                    "netbox_version"
                )
            if version and output_status(version, fmt, allow_color):
                return
            output_payload(payload, fmt, allow_color)
            return
        url = ensure_trailing_slash(build_url(base_url, args.path))
        payload = request_json("GET", url, token, params, args.timeout, verify)
        output_payload(payload, fmt, allow_color)
        return

    if args.command == "list":
        url = ensure_trailing_slash(build_url(base_url, args.endpoint))
        if args.all:
            payload = request_all(url, token, params, args.timeout, verify)
        else:
            payload = request_json("GET", url, token, params, args.timeout, verify)
        output_payload(payload, fmt, allow_color)
        return


if __name__ == "__main__":
    main()
