# Audacity MCP Server

MCP (Model Context Protocol) server for controlling Audacity through `mod-script-pipe`.

This server communicates with Audacity over named pipes and exposes many Audacity scripting commands as MCP tools.

## Features

- Connects to Audacity via `mod-script-pipe`
- Exposes a broad set of Audacity commands as MCP tools
- Uses `stdio` transport (works with Codex/Claude/Desktop clients)
- Auto-detects pipe suffixes in `/tmp` (for example `.501`)

## Requirements

- Audacity 3.x+
- Python 3.10+
- `mod-script-pipe` enabled in Audacity

## Install

```bash
git clone https://github.com/An-3/mcp-audacity.git
cd mcp-audacity
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "mcp[cli]>=1.6.0" "httpx>=0.28.1"
```

Optional (install as package + CLI entrypoint):

```bash
pip install .
audacity_mcp_server
```

## Enable mod-script-pipe in Audacity

1. Open Audacity.
2. Open the **Modules** preferences page:
   - **Windows/Linux**: `Edit -> Preferences -> Modules`
   - **macOS**: `Audacity -> Settings... -> Modules` (or `Audacity -> Preferences -> Modules` depending on build)
3. Set `mod-script-pipe` from `New` (or `Disabled`) to `Enabled`.
4. Restart Audacity.

Note: In current Audacity versions, this is configured in **Modules**, not in a separate "Scripting/Remote Control" section.

Verify pipes exist:

```bash
ls -l /tmp/audacity_script_pipe.to.* /tmp/audacity_script_pipe.from.*
```

If the files are present, Audacity is ready.

## Run the server manually

```bash
source .venv/bin/activate
python audacity_mcp_server.py
```

Expected startup logs include:

- `Audacity MCP server starting up`
- `Opened Audacity mod-script-pipe`
- `Connected to Audacity mod-script-pipe`

## Connect from Codex

Add server to Codex MCP config:

```bash
codex mcp add AudacityMCP -- /absolute/path/to/mcp-audacity/.venv/bin/python /absolute/path/to/mcp-audacity/audacity_mcp_server.py
```

List configured MCP servers:

```bash
codex mcp list
```

## Connect from Claude Desktop

Example `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "audacity": {
      "command": "/absolute/path/to/mcp-audacity/.venv/bin/python",
      "args": [
        "/absolute/path/to/mcp-audacity/audacity_mcp_server.py"
      ]
    }
  }
}
```

## Troubleshooting

- `Failed to open Audacity pipes`:
  - Confirm Audacity is running.
  - Confirm `mod-script-pipe` is `Enabled`.
  - Confirm pipe files exist in `/tmp`.
- `spawn uv ENOENT`:
  - Use absolute paths in client config, or use the Python command shown above instead of `uv`.
- Server starts but tools behave inconsistently:
  - Ensure you are using this latest version, which sends commands in `Command:` form and reads full responses until `BatchCommand finished`.

## License

MIT
