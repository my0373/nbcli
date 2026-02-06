import csv
import json
import sys

COLOR_RESET = "\033[0m"
COLOR_LABEL = "\033[36m"
COLOR_VALUE = "\033[33m"


def colorize(text, color, enabled):
    if not enabled:
        return text
    return f"{color}{text}{COLOR_RESET}"


def format_kv(payload, color):
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
    return json.dumps(payload, indent=2, sort_keys=True)


def format_yaml(payload):
    import yaml

    return yaml.safe_dump(payload, sort_keys=True)


def normalize_csv_rows(payload):
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        rows = payload["results"]
    elif isinstance(payload, list):
        rows = payload
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
    if not rows:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


def output_payload(payload, fmt, allow_color):
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


def output_status(version, fmt, allow_color):
    if fmt in ("json", "yaml", "csv"):
        return False
    label = colorize("NetBox version", COLOR_LABEL, allow_color)
    value = colorize(version, COLOR_VALUE, allow_color)
    print(f"{label}: {value}")
    return True
