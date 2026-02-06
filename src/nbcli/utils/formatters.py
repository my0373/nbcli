import csv
import json
import sys

COLOR_RESET = "\033[0m"
COLOR_LABEL = "\033[36m"
COLOR_VALUE = "\033[33m"


def colorize(text, color, enabled):
    # Apply ANSI color when enabled.
    if not enabled:
        return text
    return f"{color}{text}{COLOR_RESET}"


def format_kv(payload, color):
    # Render dictionaries as key/value lines.
    if isinstance(payload, dict):
        lines = []
        for key in sorted(payload.keys()):
            value = payload[key]
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2, sort_keys=True)
            line = (
                f"{colorize(str(key), COLOR_LABEL, color)}: "
                f"{colorize(str(value), COLOR_VALUE, color)}"
            )
            lines.append(line)
        return "\n".join(lines)
    if isinstance(payload, list):
        return "\n".join(f"- {json.dumps(item, sort_keys=True)}" for item in payload)
    return str(payload)


def format_json(payload):
    # Pretty JSON for screen use.
    return json.dumps(payload, indent=2, sort_keys=True)


def format_yaml(payload):
    # YAML output for config-friendly consumption.
    import yaml

    return yaml.safe_dump(payload, sort_keys=True)


def flatten_payload(payload, prefix=""):
    # Flatten nested dicts into dotted key paths.
    items = []
    if isinstance(payload, dict):
        for key in sorted(payload.keys()):
            value = payload[key]
            joined = f"{prefix}.{key}" if prefix else str(key)
            items.extend(flatten_payload(value, joined))
        return items
    if isinstance(payload, list):
        return [(prefix, json.dumps(payload, sort_keys=True))]
    return [(prefix, payload)]


def normalize_csv_rows(payload):
    # Map payloads into a CSV-friendly list of rows.
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        rows = payload["results"]
    elif isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        flattened = flatten_payload(payload)
        return ["key", "value"], [
            {"key": key, "value": value} for key, value in flattened
        ]
    else:
        rows = [payload]

    if not rows:
        return [], []

    headers = set()
    for row in rows:
        if isinstance(row, dict):
            headers.update(row.keys())
        else:
            headers.add("value")
    fieldnames = sorted(headers)

    cleaned_rows = []
    for row in rows:
        if isinstance(row, dict):
            cleaned = {}
            for key in fieldnames:
                value = row.get(key)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, sort_keys=True)
                cleaned[key] = value
        else:
            cleaned = {"value": row}
        cleaned_rows.append(cleaned)
    return fieldnames, cleaned_rows


def emit_csv(fieldnames, rows):
    # Write CSV to stdout.
    if not rows:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


def output_payload(payload, fmt, allow_color):
    # Dispatch output based on the selected format.
    if fmt == "json":
        print(format_json(payload))
        return
    if fmt == "yaml":
        print(format_yaml(payload))
        return
    if fmt == "csv":
        fieldnames, rows = normalize_csv_rows(payload)
        emit_csv(fieldnames, rows)
        return
    print(format_kv(payload, allow_color))
