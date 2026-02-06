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

## Usage

Check API status:

```
python nbcli.py status
```

Or, using the simple get form:

```
python nbcli.py get status
```

Get a specific object:

```
python nbcli.py get dcim/devices/1
```

List an endpoint (first page):

```
python nbcli.py list dcim/devices --param limit=50
```

List all results across pages:

```
python nbcli.py list dcim/devices --all
```

## Notes

- Use `--param key=value` multiple times for filters.
- Use `--insecure` to disable TLS verification if needed.
