#!/usr/bin/env python3
"""
audacity_mcp_pipe.py

An MCP server that connects to Audacity using the mod-script-pipe interface.
This example uses named pipes (usually located at /tmp on macOS/Linux) to send
commands and receive responses from Audacity.

Before running, ensure that Audacity’s mod-script-pipe is enabled:
  - For Audacity 3.x or later, open Preferences → Scripting (or Remote Control),
    enable the option, and restart Audacity.
  - For older versions, follow the instructions on the Audacity Wiki:
    https://wiki.audacityteam.org/wiki/Mod_script_pipe

Adjust the commands below (e.g. "GetInfo", "Record2ndTrack", "Stop") to the
actual commands supported by Audacity.
"""

import os
import time
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncIterator

from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AudacityMCPServer")

# Named pipe paths for mod-script-pipe (adjust these if your setup uses different paths)
PIPE_TO = "/tmp/audacity_script_pipe.to.501"
PIPE_FROM = "/tmp/audacity_script_pipe.from.501"

class AudacityConnection:
    """
    A simple connection that communicates with Audacity via mod-script-pipe.
    Instead of a TCP socket, we use file I/O on the named pipes.
    """
    def __init__(self, to_pipe: str, from_pipe: str):
        self.to_pipe = to_pipe
        self.from_pipe = from_pipe
        self.pipe_to = None
        self.pipe_from = None

    def connect(self) -> bool:
        """
        Open the pipes for writing commands and reading responses.
        """
        try:
            self.pipe_to = open(self.to_pipe, 'w')
            self.pipe_from = open(self.from_pipe, 'r')
            logger.info("Opened Audacity mod-script-pipe")
            return True
        except Exception as e:
            logger.error(f"Failed to open Audacity pipes: {e}")
            return False

    def disconnect(self):
        """
        Close the named pipes.
        """
        try:
            if self.pipe_to:
                self.pipe_to.close()
            if self.pipe_from:
                self.pipe_from.close()
        except Exception as e:
            logger.error(f"Error closing pipes: {e}")
        finally:
            self.pipe_to = None
            self.pipe_from = None

    def send_command(self, command: str) -> str:
        """
        Send a command string to Audacity (terminated with a newline) and
        read a single-line response.
        """
        if not (self.pipe_to and self.pipe_from):
            if not self.connect():
                raise Exception("Could not connect to Audacity mod-script-pipe")
        try:
            # Write the command followed by a newline and flush immediately.
            self.pipe_to.write(command + "\n")
            self.pipe_to.flush()
            # Wait briefly to allow Audacity to process the command.
            time.sleep(0.2)
            # Read a single line response.
            response = self.pipe_from.readline().strip()
            logger.info(f"Sent command '{command}' and received response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            self.disconnect()
            raise e

# Global variable to hold the Audacity connection.
_audacity_connection: AudacityConnection = None

def get_audacity_connection() -> AudacityConnection:
    """
    Get or create a persistent connection to Audacity.
    """
    global _audacity_connection
    if _audacity_connection is None:
        _audacity_connection = AudacityConnection(PIPE_TO, PIPE_FROM)
        if not _audacity_connection.connect():
            raise Exception("Could not open mod-script-pipe to Audacity. "
                            "Make sure Audacity’s mod-script-pipe is enabled and running.")
    return _audacity_connection

# MCP server lifespan context manager.
@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    try:
        logger.info("Audacity MCP server starting up")
        # Attempt an initial connection.
        try:
            conn = get_audacity_connection()
            logger.info("Connected to Audacity mod-script-pipe")
        except Exception as e:
            logger.warning(f"Initial connection failed: {e}")
        yield {}
    finally:
        global _audacity_connection
        if _audacity_connection:
            logger.info("Disconnecting from Audacity mod-script-pipe")
            _audacity_connection.disconnect()
            _audacity_connection = None
        logger.info("Audacity MCP server shut down")

# Create the MCP server. Customize the name and description as desired.
mcp = FastMCP(
    "AudacityMCP",
    description="MCP server to control Audacity via mod-script-pipe",
    lifespan=server_lifespan
)

# Define MCP tool endpoints.
@mcp.tool()
def get_status(ctx: Context) -> str:
    """
    Retrieve status information from Audacity.
    The command 'GetInfo' should be replaced with the actual command as documented.
    """
    try:
        conn = get_audacity_connection()
        response = conn.send_command("GetInfo")
        return response
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return f"Error: {e}"

@mcp.tool()
def start_recording(ctx: Context) -> str:
    """
    Start recording in Audacity.
    Replace 'Record2ndTrack' with the appropriate command if needed.
    """
    try:
        conn = get_audacity_connection()
        response = conn.send_command("Record2ndTrack")
        return response
    except Exception as e:
        logger.error(f"Error starting recording: {e}")
        return f"Error: {e}"

@mcp.tool()
def stop_recording(ctx: Context) -> str:
    """
    Stop recording in Audacity.
    Replace 'Stop' with the actual command as needed.
    """
    try:
        conn = get_audacity_connection()
        response = conn.send_command("Stop")
        return response
    except Exception as e:
        logger.error(f"Error stopping recording: {e}")
        return f"Error: {e}"

@mcp.tool()
def play(ctx: Context) -> str:
    """
    Start playback in Audacity.
    """
    try:
        conn = get_audacity_connection()
        response = conn.send_command("Play")
        return response
    except Exception as e:
        logger.error(f"Error starting playback: {e}")
        return f"Error: {e}"

@mcp.tool()
def pause(ctx: Context) -> str:
    """
    Pause playback in Audacity.
    """
    try:
        conn = get_audacity_connection()
        response = conn.send_command("Pause")
        return response
    except Exception as e:
        logger.error(f"Error pausing playback: {e}")
        return f"Error: {e}"

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
