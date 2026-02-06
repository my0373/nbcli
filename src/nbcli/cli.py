import argparse
import os
import sys
from urllib.parse import urlsplit, urlunsplit

import requests
from dotenv import load_dotenv

from nbcli.utils.formatters import output_payload


def load_config():
    # Load connection settings from .env.
    load_dotenv()
    base_url = os.getenv("NETBOX_URL")
    token = os.getenv("NETBOX_TOKEN")
    if not base_url or not token:
        print("Missing NETBOX_URL or NETBOX_TOKEN in .env", file=sys.stderr)
        sys.exit(2)
    return base_url, token


def build_url(base_url, path):
    # Convert relative paths into NetBox API URLs.
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = base_url.rstrip("/")
    cleaned = path.lstrip("/")
    if cleaned.startswith("api/"):
        return f"{base}/{cleaned}"
    return f"{base}/api/{cleaned}"


def ensure_trailing_slash(url):
    # NetBox endpoints are tolerant, but trailing slash keeps paging consistent.
    parts = urlsplit(url)
    path = parts.path
    if not path.endswith("/"):
        path = f"{path}/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def normalize_path(path):
    # Normalize path tokens for comparisons.
    cleaned = str(path).strip().lstrip("/")
    if cleaned.startswith("api/"):
        cleaned = cleaned[4:]
    return cleaned.rstrip("/")


def is_status_path(path):
    return normalize_path(path) == "status"


def is_cli_config_path(path):
    return normalize_path(path) == "cli config"


def mask_token(token):
    # Keep enough token context to be useful, without exposing secrets.
    if not token:
        return None
    if len(token) <= 4:
        return "*" * len(token)
    return f"{'*' * (len(token) - 4)}{token[-4:]}"


def parse_kv_list(values):
    # Parse repeated key=value flags into a dict.
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


def combine_kv_lists(*lists):
    # Merge multiple key=value lists into one params dict.
    combined = []
    for value_list in lists:
        if value_list:
            combined.extend(value_list)
    return parse_kv_list(combined)


def split_path_variants(path_parts):
    # Support multi-word paths for special targets like "cli config".
    if isinstance(path_parts, list):
        return " ".join(path_parts), "/".join(path_parts)
    return path_parts, path_parts


def extract_path_value(payload, selector):
    # Navigate dict/list structures via dot notation (e.g. .results.0.name).
    if selector is None:
        return payload
    path = selector.strip()
    if path.startswith("."):
        path = path[1:]
    if not path:
        return payload
    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(part)
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit():
                raise KeyError(part)
            index = int(part)
            try:
                current = current[index]
            except IndexError as exc:
                raise KeyError(part) from exc
        else:
            raise KeyError(part)
    return current


def request_with_errors(method, url, headers, params, timeout, verify):
    # Wrap HTTP requests with consistent error handling.
    try:
        return requests.request(
            method, url, headers=headers, params=params, timeout=timeout, verify=verify
        )
    except requests.exceptions.Timeout:
        print("Request timed out.", file=sys.stderr)
        sys.exit(3)
    except requests.exceptions.ConnectionError:
        print("Connection failed.", file=sys.stderr)
        sys.exit(3)
    except requests.exceptions.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        sys.exit(3)


def request_json(method, url, token, params, timeout, verify):
    # Fetch JSON payloads and exit cleanly on errors.
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    resp = request_with_errors(method, url, headers, params, timeout, verify)
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
    # Follow NetBox pagination and return a merged result set.
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    results = []
    next_url = url
    first_params = params
    while next_url:
        resp = request_with_errors(
            "GET", next_url, headers, first_params, timeout, verify
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


def output_selected(payload, selector, fmt, allow_color):
    # Apply optional selector before formatting output.
    try:
        selected = extract_path_value(payload, selector)
    except KeyError:
        print(f"Path not found: {selector}", file=sys.stderr)
        sys.exit(2)
    output_payload(selected, fmt, allow_color)


def main():
    # Parse shared flags first so they can appear anywhere.
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="HTTP timeout in seconds (default: 30)",
    )
    base_parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification",
    )

    format_group = base_parser.add_mutually_exclusive_group()
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

    base_args, remaining = base_parser.parse_known_args()

    parser = argparse.ArgumentParser(
        description="Interrogate a NetBox 4.4 API from the command line.",
        parents=[base_parser],
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Fetch /api/status/")

    get_parser = subparsers.add_parser(
        "get", help="GET an API path, e.g. dcim/devices/1"
    )
    get_parser.add_argument(
        "path",
        nargs="+",
        help="API path or full URL (use multiple words for special paths)",
    )
    get_parser.add_argument(
        "--param",
        action="append",
        help="Query param in key=value form (repeatable)",
    )
    get_parser.add_argument(
        "--filter",
        action="append",
        help="Filter in key=value form (repeatable)",
    )
    get_parser.add_argument(
        "--path",
        dest="select_path",
        help="Select a value using dotted path (e.g. .timeout)",
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
        "--filter",
        action="append",
        help="Filter in key=value form (repeatable)",
    )
    list_parser.add_argument(
        "--path",
        dest="select_path",
        help="Select a value using dotted path (e.g. .results.0.name)",
    )
    list_parser.add_argument(
        "--all",
        action="store_true",
        help="Follow pagination and return all results",
    )

    # Merge shared args into the final namespace.
    args = parser.parse_args(remaining)
    for key, value in vars(base_args).items():
        setattr(args, key, value)
    base_url, token = load_config()
    verify = not args.insecure
    params = combine_kv_lists(
        getattr(args, "param", None),
        getattr(args, "filter", None),
    )
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
        output_selected(payload, args.select_path, fmt, allow_color)
        return

    if args.command == "get":
        spaced_path, slashed_path = split_path_variants(args.path)
        if is_cli_config_path(spaced_path):
            payload = {
                "netbox_url": base_url,
                "token_present": bool(token),
                "token_masked": mask_token(token),
                "timeout": args.timeout,
                "insecure": bool(args.insecure),
                "format": fmt,
            }
            output_selected(payload, args.select_path, fmt, allow_color)
            return
        if is_status_path(spaced_path):
            url = ensure_trailing_slash(build_url(base_url, "status"))
            payload = request_json("GET", url, token, None, args.timeout, verify)
            output_selected(payload, args.select_path, fmt, allow_color)
            return
        url = ensure_trailing_slash(build_url(base_url, slashed_path))
        payload = request_json("GET", url, token, params, args.timeout, verify)
        output_selected(payload, args.select_path, fmt, allow_color)
        return

    if args.command == "list":
        url = ensure_trailing_slash(build_url(base_url, args.endpoint))
        if args.all:
            payload = request_all(url, token, params, args.timeout, verify)
        else:
            payload = request_json("GET", url, token, params, args.timeout, verify)
        output_selected(payload, args.select_path, fmt, allow_color)
        return


if __name__ == "__main__":
    main()
