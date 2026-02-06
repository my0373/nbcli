# nbcli

Command-line tool to interrogate a NetBox 4.4 API. Connection details are read
from `.env` in the current directory.

## Setup

1. Create `.env` with:

```
NETBOX_URL=https://your-netbox.example.com/
NETBOX_TOKEN=your_api_token
```

2. Install dependencies:

```
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .
```

## Quick start

Check API status:

```
nbcli status
```

Or run the local script directly:

```
./nbcli status
```

Get status with a specific format:

```
nbcli get status --json
```

## Commands

Get a specific object:

```
nbcli get dcim/devices/1
```

List an endpoint (first page):

```
nbcli list dcim/devices --param limit=50
```

List with filters:

```
nbcli list dcim/devices --filter role=leaf --filter site=dc1
```

List all results across pages:

```
nbcli list dcim/devices --all
```

Show CLI configuration:

```
nbcli get cli config
```

## Output formats

Default output is colorful terminal text. Use one of:

```
nbcli get status --plain
nbcli get status --json
nbcli get status --yaml
nbcli get status --csv
```

## Path selection

Use `--path` to select nested values:

```
nbcli get cli config --path .timeout
nbcli get status --path .netbox-version
nbcli list dcim/devices --path .results.0.name
```

## Notes

- Use `--param key=value` for general query params.
- Use `--filter key=value` for filters (repeatable).
- Use `--insecure` to disable TLS verification if needed.

## Examples

See `examples.md` for a catalog of API objects and example commands.

To regenerate it from the live API:

```
python scripts/generate_examples.py
```
