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
```

3. Install the CLI entrypoint:

```
uv pip install -e .
```

## Usage

Check API status:

```
nbcli status
```

Or, using the simple get form:

```
nbcli get status
```

Output formats (default is colorful terminal output):

```
nbcli get status --plain
nbcli get status --json
nbcli get status --yaml
nbcli get status --csv
```

Get a specific object:

```
nbcli get dcim/devices/1
```

List an endpoint (first page):

```
nbcli list dcim/devices --param limit=50
```

List all results across pages:

```
nbcli list dcim/devices --all
```

## Notes

- Use `--param key=value` multiple times for filters.
- Use `--insecure` to disable TLS verification if needed.
