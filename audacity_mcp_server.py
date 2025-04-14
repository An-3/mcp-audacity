#!/usr/bin/env python3
"""
audacity_mcp_pipe_full.py

An extended MCP server that connects to Audacity via the mod-script-pipe interface
and exposes a comprehensive set of Audacity scripting commands as MCP tool endpoints.

Before running, ensure that Audacity’s mod‑script‑pipe is enabled:
  - For Audacity 3.x or later, open Preferences → Scripting (or Remote Control),
    enable the option, and restart Audacity.
  - For older versions, follow the instructions on the Audacity Wiki:
    https://wiki.audacityteam.org/wiki/Mod_script_pipe

This file uses named pipes (usually in /tmp on macOS/Linux) to send commands and receive responses.
Adjust the PIPE_TO and PIPE_FROM constants below if your setup uses different paths.
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
logger = logging.getLogger("AudacityMCPServerExtended")

# Named pipe paths for mod-script-pipe (update these if needed)
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
            self.pipe_to.write(command + "\n")
            self.pipe_to.flush()
            time.sleep(0.2)  # Give Audacity time to process the command.
            response = self.pipe_from.readline().strip()
            logger.info(f"Sent command '{command}', received response: {response}")
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

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """
    Manage server startup and shutdown.
    """
    try:
        logger.info("Audacity MCP server starting up")
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

# Create the MCP server.
mcp = FastMCP(
    "AudacityMCPExtended",
    description="Extended MCP server to control Audacity via mod-script-pipe with comprehensive commands",
    lifespan=server_lifespan
)

# Helper function to create command functions with unique names.
def make_command_function(cmd_id: str, doc: str):
    def command_func(ctx: Context) -> str:
        try:
            return get_audacity_connection().send_command(cmd_id)
        except Exception as e:
            return f"Error executing {cmd_id}: {e}"
    command_func.__doc__ = doc
    command_func.__name__ = f"cmd_{cmd_id}"  # Ensure unique function name
    return command_func

# Define lists of commands by category (scripting IDs and descriptions from the Audacity Scripting Reference):
file_commands = [
    ("New", "New: Create a new empty project window."),
    ("Open", "Open: Open an audio file, list of files, or project."),
    ("Close", "Close: Close the current project window."),
    ("Save", "Save: Save the current project."),
    ("SaveAs", "SaveAs: Save the current project under a new name."),
    ("SaveCopy", "SaveCopy: Save a lossless copy of the project."),
    ("SaveCompressed", "SaveCompressed: Save a compressed copy of the project."),
    ("ExportAudio", "ExportAudio: Export audio files in various formats."),
    ("Print", "Print: Print all waveforms in the current project."),
    ("Exit", "Exit: Close all project windows and exit Audacity."),
]

import_commands = [
    ("ImportAudio", "ImportAudio: Import an audio file as a new track."),
    ("ImportLabels", "ImportLabels: Import labels into the project."),
    ("ImportMIDI", "ImportMIDI: Import a MIDI file into a note track."),
    ("ImportRaw", "ImportRaw: Import raw audio data without headers."),
]

edit_commands = [
    ("Undo", "Undo: Undo the most recent editing action."),
    ("Redo", "Redo: Redo the most recent undone action."),
    ("Cut", "Cut: Remove the selected audio and place it on the clipboard."),
    ("Delete", "Delete: Remove the selected audio without copying it."),
    ("Copy", "Copy: Copy the selected audio to the clipboard."),
    ("Paste", "Paste: Insert clipboard contents at the selection."),
    ("Duplicate", "Duplicate: Duplicate the current selection as a new clip."),
    ("EditMetaData", "EditMetaData: Edit the metadata for a track."),
    ("SplitCut", "SplitCut: Split the current clip and remove audio to right of the cut."),
    ("SplitDelete", "SplitDelete: Remove selected audio without shifting remaining audio."),
    ("Silence", "Silence: Replace selected audio with silence."),
    ("Trim", "Trim: Delete all audio except for the selected portion."),
]

label_commands = [
    ("EditLabels", "EditLabels: Open the Label Editor dialog."),
    ("AddLabel", "AddLabel: Create a new label at the selection."),
    ("PasteNewLabel", "PasteNewLabel: Paste text from the clipboard into a new label."),
    ("TypeToCreateLabel", "TypeToCreateLabel: Create a label by typing (if enabled)."),
]

select_commands = [
    ("SelectAll", "SelectAll: Select all audio in all tracks."),
    ("SelectNone", "SelectNone: Deselect all audio in all tracks."),
    ("StoreCursorPosition", "StoreCursorPosition: Store current cursor position for later selection."),
    ("SelCursorStoredCursor", "SelCursorStoredCursor: Select audio from current cursor to stored position."),
    ("ZeroCross", "ZeroCross: Adjust selection boundaries to the nearest zero crossing."),
]

view_commands = [
    ("UndoHistory", "UndoHistory: Display the undo history window."),
    ("Karaoke", "Karaoke: Display the karaoke window."),
    ("MixerBoard", "MixerBoard: Switch to the mixer board view."),
    ("ShowExtraMenus", "ShowExtraMenus: Toggle extra menus display."),
    ("ShowClipping", "ShowClipping: Toggle display of clipping in the waveform."),
    ("ZoomIn", "ZoomIn: Zoom in horizontally."),
    ("ZoomNormal", "ZoomNormal: Reset zoom to the default view."),
    ("ZoomOut", "ZoomOut: Zoom out horizontally."),
    ("ZoomSel", "ZoomSel: Zoom to fill the current selection."),
    ("ZoomToggle", "ZoomToggle: Toggle between two preset zoom levels."),
]

transport_commands = [
    ("PlayStop", "PlayStop: Toggle playback on and off."),
    ("PlayStopSelect", "PlayStopSelect: Play/Stop and update cursor position."),
    ("Pause", "Pause: Temporarily pause playback or recording."),
    ("Record1stChoice", "Record1stChoice: Start recording on the currently selected track."),
    ("Record2ndChoice", "Record2ndChoice: Start recording on a new track."),
    ("TimerRecord", "TimerRecord: Open Timer Record dialog."),
    ("PunchAndRoll", "PunchAndRoll: Start punch and roll recording."),
    ("Scrub", "Scrub: Scrub through audio."),
    ("Seek", "Seek: Jump to a specified position in the audio."),
]

effect_commands = [
    ("Amplify", "Amplify: Adjust the volume of the selected audio."),
    ("AutoDuck", "AutoDuck: Automatically lower one track's volume when another is active."),
    ("BassAndTreble", "BassAndTreble: Adjust bass and treble levels."),
    ("ChangePitch", "ChangePitch: Change pitch without changing tempo."),
    ("ChangeSpeed", "ChangeSpeed: Change both speed and pitch."),
    ("ChangeTempo", "ChangeTempo: Change tempo without affecting pitch."),
    ("ClickRemoval", "ClickRemoval: Remove clicks from the audio."),
    ("Compressor", "Compressor: Compress the dynamic range."),
    ("Distortion", "Distortion: Apply a distortion effect."),
    ("Delay", "Delay: Apply a delay effect."),
    ("Echo", "Echo: Apply an echo effect."),
    ("FadeIn", "FadeIn: Apply a linear fade-in."),
    ("FadeOut", "FadeOut: Apply a linear fade-out."),
    ("FilterCurve", "FilterCurve: Adjust frequency response using a custom curve."),
    ("GraphicEq", "GraphicEq: Apply a graphic equalizer effect."),
    ("Invert", "Invert: Invert the polarity of the audio."),
    ("LoudnessNormalization", "LoudnessNormalization: Normalize perceived loudness."),
    ("NoiseReduction", "NoiseReduction: Reduce background noise."),
    ("Normalize", "Normalize: Normalize audio volume levels."),
    ("Paulstretch", "Paulstretch: Apply an extreme time-stretch effect."),
    ("Phaser", "Phaser: Apply a phaser effect."),
    ("Repair", "Repair: Attempt to fix short clicks or glitches."),
    ("Repeat", "Repeat: Repeat the selected audio a specified number of times."),
    ("Reverb", "Reverb: Apply a reverberation effect."),
    ("Reverse", "Reverse: Reverse the selected audio."),
    ("SlidingStretch", "SlidingStretch: Continuously change tempo and/or pitch."),
    ("TruncateSilence", "TruncateSilence: Remove or compress silences."),
    ("Wahwah", "Wahwah: Apply a wahwah effect."),
]

generate_commands = [
    ("Chirp", "Chirp: Generate a chirp tone with adjustable frequency and amplitude."),
    ("DtmfTones", "DtmfTones: Generate dual-tone multi-frequency (DTMF) tones."),
    ("Noise", "Noise: Generate noise (white, pink, or brown)."),
    ("Tone", "Tone: Generate a tone of specific frequency, amplitude, and waveform."),
    ("Nyquist", "Nyquist: Open the Nyquist scripting prompt."),
    ("Pluck", "Pluck: Generate a plucked tone effect."),
    ("RhythmTrack", "RhythmTrack: Generate a rhythmic track at a specified tempo."),
    ("RissetDrum", "RissetDrum: Generate a continuously evolving drum sound."),
]

analyze_commands = [
    ("ManageAnalyzers", "ManageAnalyzers: Open the analyzers plugin manager."),
    ("ContrastAnalyser", "ContrastAnalyser: Analyze the contrast between foreground and background audio."),
    ("PlotSpectrum", "PlotSpectrum: Plot the frequency spectrum of the selected audio."),
]

tools_commands = [
    ("ManageTools", "ManageTools: Open the tools/effects/generators manager."),
    ("ManageMacros", "ManageMacros: Create or edit macros."),
    ("ApplyMacro", "ApplyMacro: Apply a defined macro to the project."),
    ("Screenshot", "Screenshot: Capture a screenshot of Audacity (short format)."),
]

transport_options_commands = [
    ("SoundActivationLevel", "SoundActivationLevel: Set the threshold level for sound-activated recording."),
    ("SoundActivation", "SoundActivation: Toggle sound-activated recording."),
]

device_commands = [
    ("InputDevice", "InputDevice: Open the recording device selection dialog."),
    ("OutputDevice", "OutputDevice: Open the playback device selection dialog."),
    ("ChangeAudio", "ChangeAudio: Open the audio host/interface selection dialog."),
]

selection_commands = [
    ("SnapToOff", "SnapToOff: Disable snapping for selections."),
    ("SnapToNearest", "SnapToNearest: Snap selections to the nearest time unit."),
    ("SnapToPrior", "SnapToPrior: Snap selections to the previous time unit."),
    ("SelStart", "SelStart: Set selection from cursor to start of track."),
    ("SelEnd", "SelEnd: Set selection from cursor to end of track."),
]

timeline_commands = [
    ("MinutesandSeconds", "MinutesandSeconds: Set timeline format to minutes and seconds."),
    ("BeatsandMeasures", "BeatsandMeasures: Set timeline format to beats and measures."),
]

focus_commands = [
    ("PrevFrame", "PrevFrame: Move focus backward from toolbars to tracks."),
    ("NextFrame", "NextFrame: Move focus forward from toolbars to tracks."),
    ("PrevTrack", "PrevTrack: Focus the previous track."),
    ("NextTrack", "NextTrack: Focus the next track."),
    ("FirstTrack", "FirstTrack: Focus the first track."),
    ("LastTrack", "LastTrack: Focus the last track."),
    ("ShiftUp", "ShiftUp: Move focus upward and select the previous track."),
    ("ShiftDown", "ShiftDown: Move focus downward and select the next track."),
    ("Toggle", "Toggle: Toggle focus on the current track."),
]

cursor_commands = [
    ("CursorLeft", "CursorLeft: Move the cursor left by one unit."),
    ("CursorRight", "CursorRight: Move the cursor right by one unit."),
    ("CursorShortJumpLeft", "CursorShortJumpLeft: Move the cursor 1 second left."),
    ("CursorShortJumpRight", "CursorShortJumpRight: Move the cursor 1 second right."),
    ("CursorLongJumpLeft", "CursorLongJumpLeft: Move the cursor 15 seconds left."),
    ("CursorLongJumpRight", "CursorLongJumpRight: Move the cursor 15 seconds right."),
]

track_commands = [
    ("TrackPan", "TrackPan: Open the pan dialog for the focused track."),
    ("TrackPanLeft", "TrackPanLeft: Pan the focused track to the left."),
    ("TrackPanRight", "TrackPanRight: Pan the focused track to the right."),
    ("TrackGain", "TrackGain: Open the gain dialog for the focused track."),
    ("TrackGainInc", "TrackGainInc: Increase the gain on the focused track."),
    ("TrackGainDec", "TrackGainDec: Decrease the gain on the focused track."),
    ("TrackMute", "TrackMute: Toggle mute on the focused track."),
    ("TrackSolo", "TrackSolo: Toggle solo on the focused track."),
    ("TrackClose", "TrackClose: Close the focused track."),
    ("TrackMoveUp", "TrackMoveUp: Move the focused track up one position."),
    ("TrackMoveDown", "TrackMoveDown: Move the focused track down one position."),
    ("TrackMoveTop", "TrackMoveTop: Move the focused track to the top."),
    ("TrackMoveBottom", "TrackMoveBottom: Move the focused track to the bottom."),
]

scriptables_I_commands = [
    ("Select", "Select: Modify selection based on parameters."),
    ("SetTrackStatus", "SetTrackStatus: Set properties (name, selected, focused) for a track."),
    ("SetTrackAudio", "SetTrackAudio: Set audio properties (mute, solo, gain, pan) for a track."),
]

scriptables_II_commands = [
    ("SetPreference", "SetPreference: Set a preference value (with optional reload)."),
    ("GetPreference", "GetPreference: Retrieve a preference value."),
    ("SetClip", "SetClip: Modify properties (color, start time) of a clip."),
    ("SetEnvelope", "SetEnvelope: Adjust the envelope value at a specified time."),
    ("SetLabel", "SetLabel: Modify an existing label."),
    ("SetProject", "SetProject: Change project window properties (size, position, caption)."),
    ("GetInfo", "GetInfo: Retrieve project information in a specified format."),
    ("Message", "Message: Send a test message to Audacity."),
    ("Help", "Help: Get help information for a command."),
    ("Import2", "Import2: Import data from a file (using a filename)."),
    ("Export2", "Export2: Export selected audio to a file with detailed options."),
    ("OpenProject2", "OpenProject2: Open a project given a filename."),
    ("SaveProject2", "SaveProject2: Save the current project with additional options."),
    ("Drag", "Drag: Simulate a mouse drag for UI interactions."),
    ("CompareAudio", "CompareAudio: Compare audio regions between tracks."),
    ("Screenshot", "Screenshot: Capture a screenshot (short format)."),
]

help_menu_commands = [
    ("QuickHelp", "QuickHelp: Display a brief help message."),
    ("Manual", "Manual: Open Audacity's manual in the default web browser."),
    ("Updates", "Updates: Check for updates for Audacity."),
    ("About", "About: Display information about Audacity."),
]

diagnostics_commands = [
    ("DeviceInfo", "DeviceInfo: Show technical information about audio devices."),
    ("MidiDeviceInfo", "MidiDeviceInfo: Show information about MIDI devices."),
    ("Log", "Log: Open the Audacity log window."),
    ("CrashReport", "CrashReport: Generate a support report for troubleshooting."),
    ("CheckDeps", "CheckDeps: Check dependencies for the current project."),
]

no_menu_commands = [
    ("PrevWindow", "PrevWindow: Navigate to the previous window."),
    ("NextWindow", "NextWindow: Navigate to the next window."),
]

# Helper to dynamically add MCP tool commands for each category.
def add_commands(cmd_list):
    for cmd_id, doc in cmd_list:
        func_name = f"cmd_{cmd_id}"
        globals()[func_name] = mcp.tool()(make_command_function(cmd_id, doc))

# Add commands by category.
add_commands(file_commands)
add_commands(import_commands)
add_commands(edit_commands)
add_commands(label_commands)
add_commands(select_commands)
add_commands(view_commands)
add_commands(transport_commands)
add_commands(effect_commands)
add_commands(generate_commands)
add_commands(analyze_commands)
add_commands(tools_commands)
add_commands(transport_options_commands)
add_commands(device_commands)
add_commands(selection_commands)
add_commands(timeline_commands)
add_commands(focus_commands)
add_commands(cursor_commands)
add_commands(track_commands)
add_commands(scriptables_I_commands)
add_commands(scriptables_II_commands)
add_commands(help_menu_commands)
add_commands(diagnostics_commands)
add_commands(no_menu_commands)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
