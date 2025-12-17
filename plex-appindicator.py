#!/usr/bin/env python3
import gi
gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
 
from gi.repository import AyatanaAppIndicator3 as AppIndicator,  Gtk, GLib
import subprocess
import signal
import os

CHECK_INTERVAL_MS = 3000  # 3 seconds

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_ICON_DIR = os.path.expanduser("~/.local/share/icons/plex")
BASE_SVG = os.path.join(BASE_ICON_DIR, "plex-base.svg")
ICON_DIR = os.path.expanduser("~/.local/share/icons/hicolor/scalable/status")

COLOR_PLACEHOLDER = "#e5a00d"  # must match the color in the base SVG

ICON_DEFS = {
    "running": {
        "name": "plex-status-running",
        "color": "#e5a00d",  # Default color - Amber Honey
    },
    "loading": {
        "name": "plex-status-loading",
        "color": "#07A0C3",  # Blue Green
    },
    "stopped": {
        "name": "plex-status-stopped",
        "color": "#DD1C1A",  # Primary Scarlet
    },
}


def ensure_status_icons():
    """
    Rebuild all status-specific SVG icons from the base Plex SVG on every startup.
    This guarantees icons always reflect the latest base SVG or color definitions.
    """
    os.makedirs(ICON_DIR, exist_ok=True)

    if not os.path.exists(BASE_SVG):
        raise FileNotFoundError(f"Base Plex SVG not found at {BASE_SVG}")

    with open(BASE_SVG, "r", encoding="utf-8") as f:
        base_svg = f.read()

    for key, info in ICON_DEFS.items():
        icon_name = info["name"]
        color = info["color"]
        out_path = os.path.join(ICON_DIR, f"{icon_name}.svg")

        # Always rebuild: replace placeholder with correct color
        svg_colored = base_svg.replace(COLOR_PLACEHOLDER, color)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_colored)
 
ensure_status_icons()

ICON_OK = ICON_DEFS["running"]["name"]
ICON_LOADING = ICON_DEFS["loading"]["name"]
ICON_BAD = ICON_DEFS["stopped"]["name"]

SERVICE_NAME = "plexmediaserver.service"
PLEX_WEB_URL = "http://localhost:32400/web"


class PlexWatcher:
    def __init__(self):
        self.current_status = "unknown"

        self.indicator = AppIndicator.Indicator.new(
            "plex-watcher",
            ICON_LOADING,  # initial icon
            AppIndicator.IndicatorCategory.SYSTEM_SERVICES,
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        # menu
        self.menu = Gtk.Menu()

        # Status line (read-only)
        self.status_item = Gtk.MenuItem(label="Checking Plex…")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)

        # Action item: dynamic "Start Plex" / "Stop Plex"
        self.action_item = Gtk.MenuItem(label="Start/Stop Plex")
        self.action_item.connect("activate", self.toggle_plex)
        self.menu.append(self.action_item)

        # Open Plex Web (only enabled when running)
        self.open_web_item = Gtk.MenuItem(label="Open Plex Web")
        self.open_web_item.connect("activate", self.open_plex_web)
        self.open_web_item.set_sensitive(False)  # disabled until we know Plex is running
        self.menu.append(self.open_web_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Open folders
        open_repo_item = Gtk.MenuItem(label="Open Code Repository")
        open_repo_item.connect("activate", self.open_repo)
        self.menu.append(open_repo_item)

        open_base_icon_item = Gtk.MenuItem(label="Open Base Icon Folder")
        open_base_icon_item.connect("activate", self.open_base_icon_folder)
        self.menu.append(open_base_icon_item)

        open_status_icons_item = Gtk.MenuItem(label="Open Status Icons Folder")
        open_status_icons_item.connect("activate", self.open_status_icons_folder)
        self.menu.append(open_status_icons_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        # first update immediately, then periodic timer
        self.update_status()
        GLib.timeout_add(CHECK_INTERVAL_MS, self.update_status)

    # ----- service status -----

    def _systemctl(self, *args) -> subprocess.CompletedProcess:
        """
        Helper to run systemctl for the Plex service.
        """
        cmd = ["systemctl", *args, SERVICE_NAME]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

    def _plex_status(self) -> str:
        """
        systemctl is-active plexmediaserver.service
        -> active, inactive, failed, activating, etc.
        """
        try:
            result = subprocess.run(
                ["systemctl", "is-active", SERVICE_NAME],
                capture_output=True,
                text=True,
                check=False,
            )
            status = result.stdout.strip()
            return status or "unknown"
        except Exception:
            return "unknown"

    # ----- start/stop actions -----

    def toggle_plex(self, _widget):
        """
        Called when the Start/Stop menu item is clicked.
        Uses current_status to decide whether to start or stop.
        """
        status = self.current_status

        if status == "active":
            # Stop Plex
            self._set_loading("Stopping Plex…")
            result = self._systemctl("stop")
        else:
            # Start Plex
            self._set_loading("Starting Plex…")
            result = self._systemctl("start")

        if result.returncode != 0:
            # Show error in status line
            msg = result.stderr.strip() or "systemctl error"
            self.status_item.set_label(f"Error: {msg}")

        # We'll get the updated status on the next timer tick,
        # but do one immediate refresh too.
        self.update_status()

    # ----- open folder/URL actions -----

    def _xdg_open(self, path: str):
        """Open a path or URL with xdg-open."""
        subprocess.Popen(["xdg-open", path], start_new_session=True)

    def open_plex_web(self, _widget):
        self._xdg_open(PLEX_WEB_URL)

    def open_repo(self, _widget):
        self._xdg_open(REPO_DIR)

    def open_base_icon_folder(self, _widget):
        self._xdg_open(BASE_ICON_DIR)

    def open_status_icons_folder(self, _widget):
        self._xdg_open(ICON_DIR)

    # ----- UI update -----

    def _set_loading(self, label: str):
        self.indicator.set_icon_full(ICON_LOADING, label)
        self.status_item.set_label(label)
        # keep action enabled, but label may still say Start/Stop

    def update_status(self):
        status = self._plex_status()
        self.current_status = status

        if status == "active":
            # Plex running
            self.indicator.set_icon_full(ICON_OK, "Plex is running")
            self.status_item.set_label("Plex: RUNNING")
            self.action_item.set_label("Stop Plex")
            self.action_item.set_sensitive(True)
            self.open_web_item.set_sensitive(True)

        elif status in ("activating", "reloading", "unknown"):
            # Starting / reloading / unknown → treat as loading
            self.indicator.set_icon_full(ICON_LOADING, "Plex starting / checking")
            self.status_item.set_label(f"Plex: STARTING ({status})")
            self.action_item.set_sensitive(False)
            self.action_item.set_label("Stop Plex")
            self.open_web_item.set_sensitive(False)

        else:
            # inactive, failed, deactivating, etc.
            self.indicator.set_icon_full(ICON_BAD, f"Plex is {status}")
            self.status_item.set_label(f"Plex: {status.upper()}")
            self.action_item.set_label("Start Plex")
            self.action_item.set_sensitive(True)
            self.open_web_item.set_sensitive(False)

        return True  # keep timer running

    # ----- cleanup -----

    def cleanup(self):
        try:
            self.indicator.set_status(AppIndicator.IndicatorStatus.PASSIVE)
        except Exception:
            pass

    def quit(self, _widget=None):
        self.cleanup()
        Gtk.main_quit()
        return False  # for GLib signal handlers


def main():
    watcher = PlexWatcher()

    # Use GLib to catch signals in the main loop
    GLib.unix_signal_add(
        GLib.PRIORITY_DEFAULT, signal.SIGINT, watcher.quit, None
    )
    GLib.unix_signal_add(
        GLib.PRIORITY_DEFAULT, signal.SIGTERM, watcher.quit, None
    )

    Gtk.main()


if __name__ == "__main__":
    main()
