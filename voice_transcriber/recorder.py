#!/usr/bin/env python3
"""
Meeting Recorder - One-Click Recording for Bill

Simple menu bar app that records meetings and saves to OneDrive.
Uses sounddevice (no portaudio dependency issues).

Usage:
    python3 recorder.py        # Menu bar app
    python3 recorder.py --cli  # Command line mode
"""

import os
import sys
import threading
import time
import numpy as np
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Where recordings are saved - syncs to Lukas's system
RECORDINGS_FOLDER = Path.home() / "Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming"

# Audio settings
SAMPLE_RATE = 44100
CHANNELS = 1

# =============================================================================
# IMPORTS
# =============================================================================

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("Installing required packages...")
    os.system("pip3 install sounddevice soundfile")
    import sounddevice as sd
    import soundfile as sf

# Optional: Menu bar support
try:
    import rumps
    HAS_RUMPS = True
except ImportError:
    HAS_RUMPS = False
    print("Note: Install 'rumps' for menu bar support: pip3 install rumps")

# =============================================================================
# RECORDER CLASS
# =============================================================================

class MeetingRecorder:
    """Records audio and saves to WAV file."""

    def __init__(self, output_folder: Path):
        self.output_folder = output_folder
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.is_recording = False
        self.frames = []
        self.current_file = None
        self.start_time = None
        self.stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        """Called for each audio block during recording."""
        if status:
            print(f"Audio status: {status}")
        if self.is_recording:
            self.frames.append(indata.copy())

    def start_recording(self) -> str:
        """Start recording. Returns the output filename."""
        if self.is_recording:
            return str(self.current_file)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.output_folder / f"meeting_{timestamp}.wav"

        self.frames = []
        self.start_time = time.time()
        self.is_recording = True

        # Start recording stream
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=self._audio_callback
        )
        self.stream.start()

        print(f"🔴 Recording started: {self.current_file.name}")
        return str(self.current_file)

    def stop_recording(self) -> tuple:
        """Stop recording and save. Returns (filepath, duration)."""
        if not self.is_recording:
            return None, 0

        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0

        # Stop stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Save audio
        if self.frames and self.current_file:
            audio_data = np.concatenate(self.frames, axis=0)
            sf.write(str(self.current_file), audio_data, SAMPLE_RATE)
            print(f"✅ Saved: {self.current_file.name} ({int(duration)}s)")
            return str(self.current_file), duration

        return None, 0

    def get_duration(self) -> float:
        """Get current recording duration in seconds."""
        if self.is_recording and self.start_time:
            return time.time() - self.start_time
        return 0

    def get_duration_str(self) -> str:
        """Get duration as MM:SS string."""
        secs = int(self.get_duration())
        return f"{secs // 60:02d}:{secs % 60:02d}"

# =============================================================================
# MENU BAR APP
# =============================================================================

if HAS_RUMPS:
    class RecorderApp(rumps.App):
        """Menu bar recording app."""

        def __init__(self):
            super().__init__("🎙️", quit_button=None)

            self.recorder = MeetingRecorder(RECORDINGS_FOLDER)
            self.timer = None

            # Menu items
            self.record_btn = rumps.MenuItem("▶️ Start Recording", callback=self.toggle)
            self.status = rumps.MenuItem("Ready")
            self.status.set_callback(None)
            self.folder_btn = rumps.MenuItem("📁 Open Folder", callback=self.open_folder)
            self.quit_btn = rumps.MenuItem("Quit", callback=self.quit_app)

            self.menu = [self.record_btn, None, self.status, None, self.folder_btn, self.quit_btn]

        def toggle(self, _):
            """Toggle recording on/off."""
            if not self.recorder.is_recording:
                # Start
                self.recorder.start_recording()
                self.title = "🔴"
                self.record_btn.title = "⏹️ Stop Recording"
                self.status.title = "Recording: 00:00"

                self.timer = rumps.Timer(self.update_time, 1)
                self.timer.start()

                rumps.notification("Recording Started", "", "Click 🔴 to stop")
            else:
                # Stop
                filepath, duration = self.recorder.stop_recording()
                self.title = "🎙️"
                self.record_btn.title = "▶️ Start Recording"

                if self.timer:
                    self.timer.stop()

                if filepath:
                    mins, secs = int(duration) // 60, int(duration) % 60
                    self.status.title = f"Saved: {mins}:{secs:02d}"
                    rumps.notification("Recording Saved!", f"{mins}:{secs:02d}", "Will be transcribed automatically")
                else:
                    self.status.title = "Ready"

        def update_time(self, _):
            """Update duration display."""
            if self.recorder.is_recording:
                self.status.title = f"Recording: {self.recorder.get_duration_str()}"

        def open_folder(self, _):
            """Open recordings folder."""
            os.system(f'open "{RECORDINGS_FOLDER}"')

        def quit_app(self, _):
            """Quit."""
            if self.recorder.is_recording:
                self.recorder.stop_recording()
            rumps.quit_application()

# =============================================================================
# CLI MODE
# =============================================================================

def run_cli():
    """Command-line recording mode."""
    print("\n" + "=" * 50)
    print("  🎙️ MEETING RECORDER")
    print("=" * 50)
    print(f"\nRecordings save to:\n{RECORDINGS_FOLDER}\n")

    recorder = MeetingRecorder(RECORDINGS_FOLDER)

    try:
        input("Press ENTER to start recording...")
        recorder.start_recording()
        print("\n🔴 RECORDING - Press ENTER to stop\n")

        # Show duration while recording
        while True:
            time.sleep(1)
            print(f"\r  Duration: {recorder.get_duration_str()}  ", end="", flush=True)

            # Check for input (non-blocking check)
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                input()
                break

    except KeyboardInterrupt:
        print("\n\nStopping...")

    filepath, duration = recorder.stop_recording()
    if filepath:
        print(f"\n\n✅ Recording saved!")
        print(f"   File: {Path(filepath).name}")
        print(f"   Duration: {int(duration)}s")
        print(f"\n   → Will be transcribed automatically!\n")

# =============================================================================
# MAIN
# =============================================================================

def main():
    # Ensure folder exists
    RECORDINGS_FOLDER.mkdir(parents=True, exist_ok=True)

    if "--cli" in sys.argv:
        run_cli()
    elif HAS_RUMPS:
        print(f"\n🎙️ Meeting Recorder starting...")
        print(f"📁 Recordings: {RECORDINGS_FOLDER}")
        print(f"\nLook for 🎙️ in your menu bar!\n")
        RecorderApp().run()
    else:
        print("Menu bar mode requires 'rumps'. Install with: pip3 install rumps")
        print("Running in CLI mode instead...\n")
        run_cli()

if __name__ == "__main__":
    main()
