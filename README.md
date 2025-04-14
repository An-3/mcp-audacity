# Audacity MCP Server

This project implements an MCP (Model Context Protocol) server that connects to Audacity via its mod‑script‑pipe interface. Using named pipes, the server sends commands to Audacity and receives responses, allowing you to control Audacity (for example, starting/stopping recording or playback) through MCP endpoints. The server can be launched using the `uv` tool and integrated with the Claude Desktop client.

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation and Setup](#installation-and-setup)
4. [Configuring Audacity](#configuring-audacity)
5. [Usage](#usage)
6. [Configuration with Claude Desktop Client](#configuration-with-claude-desktop-client)
7. [Troubleshooting](#troubleshooting)
8. [License](#license)

## Features

- **Audacity Integration:** Communicates with Audacity using the mod‑script‑pipe interface via named pipes.
- **MCP Endpoints:** Provides MCP tool endpoints to:
  - Retrieve Audacity status.
  - Start and stop recording.
  - Play and pause playback.
- **uv Integration:** Uses the `uv` tool to run the MCP server.
- **Claude Desktop Compatibility:** Can be configured to launch using the Claude Desktop client.

## Requirements

- **Audacity:** Version 3.x or later is recommended.
- **Python:** Version 3.13 or newer.
- **uv Tool:** For running the MCP server.
- **mod‑script‑pipe:** Audacity’s remote control/scripting interface must be enabled.
- **Python Dependencies:** The project requires the following packages:
  - `httpx`
  - `mcp[cli]`

## Installation-and-Setup

1. **Clone or Download the Project:**

   ```
   git clone <repository-url>
   cd mcp-audacity
   ```

2. **Set Up a Virtual Environment:**
- **Use the uv tool to create and activate the virtual environment:**

   ```
   uv venv --python=python3.13
   source .venv/bin/activate
   ```

3. **Install Dependencies**
- Install the required dependencies with:
   ```
   uv add "mcp[cli]" httpx
   ```

4. **Verify the Project Structure**  
Make sure your project folder contains at least:
- `audacity_mcp_pipe.py` (the main MCP server script)
- `pyproject.toml` (project configuration)
- (Optional) `claude_desktop_config.json` (for integration with the Claude Desktop client)

## Configuring-Audacity
- For the MCP server to connect with Audacity, its mod‑script‑pipe interface must be enabled.

**Step 1: Enable mod‑script‑pipe in Audacity**
- Open Audacity.
 - Open Preferences:
 - On macOS: Click Audacity > Preferences…
 - On Windows: Click Edit > Preferences…
- Navigate to the Scripting/Remote Control Section:
- Look for an option such as Enable mod‑script‑pipe or Enable Remote Control/Scripting.
- Enable the feature.
- Restart Audacity.

**Step 2: Verify Named Pipes**
- Audacity should create two named pipes (by default on macOS/Linux):
 - Command pipe: `/tmp/audacity_script_pipe.to.%number%`
 - Response pipe: `/tmp/audacity_script_pipe.from.%number%`
- Run the following command in a terminal to verify:

   ```
   ls -l /tmp | grep audacity_script_pipe
   ```
> If you see extra numbers or characters (e.g. `/tmp/audacity_script_pipe.to.1234`), update the pipe paths in your `audacity_mcp_pipe.py` accordingly.

## Usage
- Running the MCP Server from the Command Line
**1. Navigate to Your Project Directory:**

   ```MacOS
   cd /%path_to_project%/mcp-audacity
   ```

**2. Activate the Virtual Environment (if not already activated):**

   ```MacOS
   source .venv/bin/activate
   ```

**3. Launch the Server with the uv Tool:** 

   ```MacOS
   uv run audacity_mcp_pipe.py
   ```

- You should see log messages such as:

   ```MacOS
   2025-04-13 19:36:32,759 - AudacityMCPServer - INFO - Audacity MCP server starting up
   2025-04-13 19:36:32,760 - AudacityMCPServer - INFO - Opened Audacity mod-script-pipe
   2025-04-13 19:36:32,762 - AudacityMCPServer - INFO - Connected to Audacity mod-script-pipe
   ```

## MCP Endpoints
- Your MCP server exposes several endpoints that can be invoked by an MCP client. For example:

- get_status: Retrieves Audacity status.
- start_recording: Starts recording.
- stop_recording: Stops recording.
- play: Starts playback.
- pause: Pauses playback.  

- These endpoints are defined in `audacity_mcp_pipe.py` and can be triggered using an MCP client.

## Configuration with Claude Desktop Client
- If you want to run your server via the Claude Desktop client, update your `claude_desktop_config.json` to point to this project. For example:

  ```
  {
    "mcpServers": {
        "audacity": {
        "command": "/%absolute_path_to_ev%/.local/bin/uv",
        "args": [
            "--directory",
            "/Users/andriiboboshko/mcp-audacity",
            "run",
            "audacity_mcp_pipe.py"
        ]
        }
    }
  }
  ```
  
- Ensure the paths match your project location and that your virtual environment is set up correctly.

## License
This project is provided under MIT License. Feel free to modify and distribute as needed.

## Troubleshooting

**Error: spawn uv ENOENT**
- I found that it can occur when MCP server tried to launch uv and despite uv was in my PATH it did not create a process. It fixed when I added an absolute path to uv in the Claude Desktop config `claude_desktop_config.json`.

**ERROR - Failed to connect to Audacity: [Errno 61] Connection refused**
- I've got this error because Audacity created command and response pipes files in the /tmp folder with some numbers:

   ```
   /tmp/audacity_script_pipe.to.501
   /tmp/audacity_script_pipe.from.501
   ```
- After updating the code with the particular number it worked. 
