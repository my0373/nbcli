import argparse
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

import requests
from dotenv import load_dotenv

from nbcli.utils.formatters import output_payload, serialize_payload


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


def join_url(base, path):
    # Join a base URL with a path segment.
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


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


def request_all_safe(url, token, timeout, verify):
    # Fetch all pages and return errors instead of exiting.
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    results = []
    next_url = url
    while next_url:
        resp = request_with_errors("GET", next_url, headers, None, timeout, verify)
        if not resp.ok:
            return {"error": resp.text, "status": resp.status_code}
        try:
            payload = resp.json()
        except ValueError:
            return {"error": resp.text, "status": resp.status_code}
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


def fetch_api_root(base_url, token, timeout, verify):
    # Fetch the NetBox API root listing.
    url = ensure_trailing_slash(f"{base_url.rstrip('/')}/api")
    return request_json("GET", url, token, None, timeout, verify)


def dump_all_objects(base_url, token, timeout, verify):
    # Retrieve every API object and return a nested dict.
    return dump_all_objects_filtered(base_url, token, timeout, verify, include_all=True)


def dump_all_objects_filtered(base_url, token, timeout, verify, include_all):
    # Retrieve API objects and optionally skip noisy endpoints.
    root = fetch_api_root(base_url, token, timeout, verify)
    dump = {}
    excluded = {"core/jobs", "core/object-changes"}
    for app, url in sorted(root.items()):
        if app == "status":
            continue
        app_payload = request_json("GET", url, token, None, timeout, verify)
        endpoints = sorted(app_payload.keys()) if isinstance(app_payload, dict) else []
        dump[app] = {}
        for endpoint in endpoints:
            if not include_all and f"{app}/{endpoint}" in excluded:
                continue
            endpoint_url = ensure_trailing_slash(join_url(url, endpoint))
            dump[app][endpoint] = request_all_safe(
                endpoint_url, token, timeout, verify
            )
    return dump


def fetch_api_index(base_url, token, timeout, verify):
    # Retrieve app -> endpoint list from the API root.
    root = fetch_api_root(base_url, token, timeout, verify)
    index = {}
    for app, url in sorted(root.items()):
        if app == "status":
            continue
        app_payload = request_json("GET", url, token, None, timeout, verify)
        endpoints = sorted(app_payload.keys()) if isinstance(app_payload, dict) else []
        index[app] = endpoints
    return index


def build_show_payload(kind, base_url, token, timeout, verify):
    # Build the payload for `show`.
    verbs = ["status", "get", "list", "dump", "show"]
    if kind in ("verbs", "commands"):
        return {"verbs": verbs}
    index = fetch_api_index(base_url, token, timeout, verify)
    if kind == "apps":
        return {"apps": sorted(index.keys())}
    if kind in ("endpoints", "get", "list"):
        flat = []
        for app, endpoints in sorted(index.items()):
            for endpoint in endpoints:
                flat.append(f"{app}/{endpoint}")
        return {"endpoints": flat}
    query = kind.lower()
    matches = []
    for app, endpoints in sorted(index.items()):
        for endpoint in endpoints:
            path = f"{app}/{endpoint}"
            if query in path.lower():
                matches.append(path)
    return {"endpoints": matches}


def build_dump_payload(base_url, token, timeout, verify, include_all):
    # Wrap dump data with metadata.
    status_url = ensure_trailing_slash(build_url(base_url, "status"))
    status = request_json("GET", status_url, token, None, timeout, verify)
    hostname = status.get("hostname", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    local_tz = os.environ.get("TZ")
    if not local_tz:
        local_tz = str(datetime.now().astimezone().tzinfo)
    nb_id = urlsplit(base_url).hostname or "unknown"
    if nb_id != "unknown":
        nb_id = nb_id.split(".")[0]
    return {
        "netbox_data": {
            "hostname": hostname,
            "dump_datetime": timestamp,
            "dump_timezone": local_tz,
            "nb_id": nb_id,
            "data": dump_all_objects_filtered(
                base_url, token, timeout, verify, include_all
            ),
        }
    }


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
    list_parser.add_argument(
        "endpoint", nargs="?", help="API endpoint, e.g. dcim/devices"
    )
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

    dump_parser = subparsers.add_parser(
        "dump", help="Dump all API objects to a file"
    )
    dump_parser.add_argument(
        "filename",
        help="Output filename (YAML by default)",
    )
    dump_parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include jobs and object-changes in the dump",
    )

    show_parser = subparsers.add_parser(
        "show", help="Show options for a given verb"
    )
    show_parser.add_argument(
        "target",
        nargs="?",
        help="What to show (verbs, apps, endpoints, get, list, or a search term)",
    )
    show_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all endpoints (equivalent to 'show endpoints')",
    )
    show_parser.add_argument(
        "--path",
        dest="select_path",
        help="Select a value using dotted path (e.g. .apps.0)",
    )

    # Merge shared args into the final namespace.
    args = parser.parse_args(remaining)
    for key, value in vars(base_args).items():
        if value != base_parser.get_default(key):
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
        if not args.endpoint:
            payload = build_show_payload(
                "endpoints", base_url, token, args.timeout, verify
            )
            output_selected(payload, args.select_path, fmt, allow_color)
            return
        url = ensure_trailing_slash(build_url(base_url, args.endpoint))
        if args.all:
            payload = request_all(url, token, params, args.timeout, verify)
        else:
            payload = request_json("GET", url, token, params, args.timeout, verify)
        output_selected(payload, args.select_path, fmt, allow_color)
        return

    if args.command == "dump":
        dump_fmt = "yaml" if fmt == "pretty" else fmt
        if dump_fmt in ("plain", "csv"):
            print("Dump output supports YAML or JSON only.", file=sys.stderr)
            sys.exit(2)
        payload = build_dump_payload(
            base_url, token, args.timeout, verify, args.include_all
        )
        content = serialize_payload(payload, dump_fmt)
        with open(args.filename, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Wrote {args.filename}")
        return

    if args.command == "show":
        if args.all:
            target = "endpoints"
        else:
            target = args.target
        if not target:
            print("show: error: the following arguments are required: target", file=sys.stderr)
            sys.exit(2)
        try:
            payload = build_show_payload(
                target, base_url, token, args.timeout, verify
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(2)
        output_selected(payload, args.select_path, fmt, allow_color)
        return


if __name__ == "__main__":
    main()
