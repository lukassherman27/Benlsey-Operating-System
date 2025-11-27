#!/usr/bin/env python3
"""
Meeting Recorder - Simple Menu Bar App for Recording Meetings

Bill runs this on his Mac. Records audio and saves directly to
OneDrive folder that syncs to Lukas's system for processing.

Usage:
    python3 meeting_recorder.py        # Menu bar app
    python3 meeting_recorder.py --cli  # Command line version

Requirements:
    pip3 install pyaudio rumps
"""

import os
import sys
import wave
import threading
import time
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION - UPDATE THESE PATHS
# =============================================================================

# TODO: Update this path once Bensley OneDrive is set up
# For Bill's Mac, this would be something like:
#   ~/Library/CloudStorage/OneDrive-BensleyDesignStudios/Voice Memos
#
# For now, using a local folder that can be changed later
RECORDINGS_FOLDER = Path.home() / "Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming"

# Alternative paths (uncomment the right one once set up):
# RECORDINGS_FOLDER = Path.home() / "Library/CloudStorage/OneDrive-BensleyDesignStudios/Voice Memos"
# RECORDINGS_FOLDER = Path.home() / "OneDrive - Bensley Design Studios/Voice Memos"

# =============================================================================
# AUDIO SETTINGS
# =============================================================================

SAMPLE_RATE = 44100
CHANNELS = 1  # Mono for voice
CHUNK_SIZE = 1024

# =============================================================================
# IMPORTS (with auto-install)
# =============================================================================

try:
    import pyaudio
    PYAUDIO_FORMAT = pyaudio.paInt16
except ImportError:
    print("Installing pyaudio...")
    os.system("pip3 install pyaudio")
    import pyaudio
    PYAUDIO_FORMAT = pyaudio.paInt16

try:
    import rumps
    HAS_RUMPS = True
except ImportError:
    print("Menu bar mode requires 'rumps'. Install with: pip3 install rumps")
    print("Running in CLI mode instead.\n")
    HAS_RUMPS = False

# =============================================================================
# RECORDER CLASS
# =============================================================================

class MeetingRecorder:
    """Simple audio recorder that saves to OneDrive."""

    def __init__(self, output_folder: Path):
        self.output_folder = output_folder
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.current_file = None
        self.start_time = None

    def start_recording(self) -> str:
        """Start recording. Returns filename."""
        if self.is_recording:
            return str(self.current_file)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.output_folder / f"meeting_{timestamp}.wav"

        self.frames = []
        self.start_time = time.time()

        # Open audio stream
        self.stream = self.audio.open(
            format=PYAUDIO_FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

        self.is_recording = True

        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record_loop)
        self.recording_thread.start()

        return str(self.current_file)

    def _record_loop(self):
        """Background thread for audio capture."""
        while self.is_recording:
            try:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break

    def stop_recording(self) -> tuple:
        """Stop and save. Returns (filepath, duration_seconds)."""
        if not self.is_recording:
            return None, 0

        self.is_recording = False

        if self.recording_thread:
            self.recording_thread.join(timeout=2)

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        duration = time.time() - self.start_time if self.start_time else 0

        # Save WAV file
        if self.frames and self.current_file:
            with wave.open(str(self.current_file), 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(PYAUDIO_FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b''.join(self.frames))

            return str(self.current_file), duration

        return None, 0

    def get_duration_str(self) -> str:
        """Get current recording duration as MM:SS."""
        if not self.is_recording or not self.start_time:
            return "00:00"
        elapsed = int(time.time() - self.start_time)
        return f"{elapsed // 60:02d}:{elapsed % 60:02d}"

    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.close()
        self.audio.terminate()

# =============================================================================
# MENU BAR APP
# =============================================================================

if HAS_RUMPS:
    class MeetingRecorderApp(rumps.App):
        """Menu bar app for recording meetings."""

        def __init__(self):
            super().__init__("🎙️", quit_button=None)

            self.recorder = MeetingRecorder(RECORDINGS_FOLDER)
            self.timer = None

            self.start_button = rumps.MenuItem("▶️ Start Recording", callback=self.toggle_recording)
            self.status_item = rumps.MenuItem("Ready to record")
            self.status_item.set_callback(None)
            self.folder_button = rumps.MenuItem("📁 Open Recordings Folder", callback=self.open_folder)
            self.quit_button = rumps.MenuItem("Quit", callback=self.quit_app)

            self.menu = [
                self.start_button,
                None,
                self.status_item,
                None,
                self.folder_button,
                self.quit_button
            ]

        def toggle_recording(self, sender):
            """Start or stop recording."""
            if not self.recorder.is_recording:
                # Start
                filepath = self.recorder.start_recording()
                self.title = "🔴"
                self.start_button.title = "⏹️ Stop Recording"
                self.status_item.title = "Recording: 00:00"

                self.timer = rumps.Timer(self.update_duration, 1)
                self.timer.start()

                rumps.notification(
                    title="Recording Started",
                    subtitle="Meeting is being recorded",
                    message=Path(filepath).name
                )
            else:
                # Stop
                filepath, duration = self.recorder.stop_recording()
                self.title = "🎙️"
                self.start_button.title = "▶️ Start Recording"

                if self.timer:
                    self.timer.stop()
                    self.timer = None

                if filepath:
                    mins, secs = int(duration) // 60, int(duration) % 60
                    self.status_item.title = f"Last: {mins}:{secs:02d}"

                    rumps.notification(
                        title="Recording Saved!",
                        subtitle=f"Duration: {mins}:{secs:02d}",
                        message="Will sync automatically"
                    )
                else:
                    self.status_item.title = "Ready to record"

        def update_duration(self, timer):
            """Update duration display."""
            if self.recorder.is_recording:
                self.status_item.title = f"Recording: {self.recorder.get_duration_str()}"

        def open_folder(self, sender):
            """Open recordings folder."""
            os.system(f'open "{RECORDINGS_FOLDER}"')

        def quit_app(self, sender):
            """Quit app."""
            if self.recorder.is_recording:
                self.recorder.stop_recording()
            self.recorder.cleanup()
            rumps.quit_application()

# =============================================================================
# CLI VERSION
# =============================================================================

def run_cli():
    """Simple command-line recorder."""
    print("\n" + "=" * 50)
    print("  MEETING RECORDER")
    print("=" * 50)
    print(f"\nRecordings save to:\n{RECORDINGS_FOLDER}\n")

    recorder = MeetingRecorder(RECORDINGS_FOLDER)

    try:
        input("Press ENTER to start recording...")
        filepath = recorder.start_recording()
        print(f"\n🔴 RECORDING: {Path(filepath).name}")
        print("Press ENTER to stop...\n")

        # Show duration
        while True:
            if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:
                input()
                break
            print(f"\r  {recorder.get_duration_str()}", end="", flush=True)

    except (KeyboardInterrupt, NameError):
        # NameError if select not imported, just wait for input
        try:
            input()
        except:
            pass

    filepath, duration = recorder.stop_recording()

    if filepath:
        print(f"\n\n✅ Saved: {Path(filepath).name}")
        print(f"   Duration: {int(duration//60)}:{int(duration%60):02d}")
        print(f"   Location: {RECORDINGS_FOLDER}")
        print(f"\n   → Will sync to processing system automatically!")

    recorder.cleanup()

# =============================================================================
# MAIN
# =============================================================================

def main():
    # Ensure folder exists
    if not RECORDINGS_FOLDER.exists():
        print(f"Creating recordings folder: {RECORDINGS_FOLDER}")
        RECORDINGS_FOLDER.mkdir(parents=True, exist_ok=True)

    # Check mode
    if "--cli" in sys.argv or not HAS_RUMPS:
        try:
            import select
        except ImportError:
            pass
        run_cli()
    else:
        print(f"\n🎙️ Meeting Recorder")
        print(f"Recordings: {RECORDINGS_FOLDER}")
        print(f"\nLook for 🎙️ in your menu bar!\n")

        app = MeetingRecorderApp()
        app.run()

if __name__ == "__main__":
    main()
