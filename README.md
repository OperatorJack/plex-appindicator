# Plex AppIndicator

A small Python script that adds a Plex status and control icon to your GNOME top bar using an Ayatana AppIndicator.

The indicator:

- Shows whether the `plexmediaserver.service` systemd service is:
  - **Running** (Plex up)
  - **Starting / reloading** (loading)
  - **Stopped / failed**
- Lets you **Start** / **Stop** Plex directly from the indicator menu.
- Uses a **single base SVG Plex icon**, recolored at runtime into:
  - Running (default Plex color)
  - Loading (blue/teal)
  - Stopped (red)

Tested on **Ubuntu 25** with GNOME and the AppIndicator/KStatusNotifier extension enabled.

 
## Requirements

### System / Desktop:

- Ubuntu 25 or similar GNOME-based system
- GNOME AppIndicator support

    Install with:
    ```bash
    sudo apt install gnome-shell-extension-appindicator
    ```
    Then enable the extension using GNOME Extensions or Extension Manager.

Python and GI packages:
```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 libayatana-appindicator3-1
```

### Repository contains:
- plex-appindicator.py
- plex-base.svg (raw single-color SVG used for recoloring)
- install.sh (quick installation script if preferred)
- restart.sh (quick restart of indicator, useful when debugging changes)

## How the Icon System Works
The script loads plex-base.svg.

It looks for a specific color placeholder (default: #e5a00d).

It generates three recolored icons:
- plex-status-running.svg
- plex-status-loading.svg
- plex-status-stopped.svg

These icons are written to:
~/.local/share/icons/hicolor/scalable/status

GNOME loads them as icon theme entries named:
- plex-status-running
- plex-status-loading
- plex-status-stopped

The indicator swaps among these icons based on Plex status.

## Installation
## Automated Installation
Clone the repository and navigate to it via terminal. Run:
```bash
chmod +x install.sh
./install.sh
```

You should see an output similar to:
```
user@pc:~/git/plex-appindicator$ ./install.sh 
Repo directory:        /home/user/git/plex-appindicator
Script path:           /home/user/git/plex-appindicator/plex-appindicator.py
Service template:      /home/user/git/plex-appindicator/plex-watcher.service
Systemd service dest:  /home/user/.config/systemd/user/plex-watcher.service
Base SVG src:          /home/user/git/plex-appindicator/plex-base.svg
Base SVG dest:         /home/user/.local/share/icons/plex/plex-base.svg

Copied plex-base.svg to /home/user/.local/share/icons/plex/plex-base.svg
Marked /home/user/git/plex-appindicator/plex-appindicator.py as executable
Wrote systemd unit to /home/user/.config/systemd/user/plex-watcher.service
Created symlink '/home/user/.config/systemd/user/default.target.wants/plex-watcher.service' to '/home/user/.config/systemd/user/plex-watcher.service'.

Installation complete.
The Plex AppIndicator service is now running as a user service.
You can check status with:
  systemctl --user status plex-watcher.service
```

## Manual Installation
Step 1 – Clone the repository:
git clone https://github.com/OperatorJack/plex-appindicator.git

```bash
cd plex-appindicator
```

Step 2 – Install the base SVG:
```bash
mkdir -p ~/.local/share/icons/plex
cp plex-base.svg ~/.local/share/icons/plex/plex-base.svg
```

Step 3 – Make the script executable:
```bash
chmod +x plex-appindicator.py
```

Step 4 – Test run in terminal:
```bash
./plex-appindicator.py
```

You should now see:
- An icon in the top bar
- A menu showing status and Start/Stop options when you click on the icon

If icon does not appear, verify AppIndicator extension is enabled in GNOME.

### Running as a systemd User Service
This allows the indicator to start automatically when you log in.

Step 1 – Create service directory:
```bash
mkdir -p ~/.config/systemd/user
```

Step 2 – Create file:
```bash
touch ~/.config/systemd/user/plex-appindicator.service
```

Paste into the file:

```
[Unit]
Description=Plex status and control AppIndicator

[Service]
ExecStart=/absolute/path/to/plex-appindicator.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```

> Replace the ExecStart path with the actual path to the script in your repository.

Step 3 – Reload systemd and enable the service:
```bash
systemctl --user daemon-reload
systemctl --user enable --now plex-appindicator.service
```

The indicator will now autostart at login.

## Checking Logs
To check service status:
```bash
systemctl --user status plex-appindicator.service
```

To view logs:
```bash
journalctl --user -u plex-appindicator.service -e
```

You may see a warning: `libayatana-appindicator is deprecated`.

This is expected and harmless. It comes from upstream C library code.

## Permissions for Start/Stop

The script uses:
```bash
systemctl is-active plexmediaserver.service
systemctl start plexmediaserver.service
systemctl stop plexmediaserver.service
```

If your user can run those commands without sudo, the indicator works normally.

If not, you may need:

To run Plex as a user service instead of system service, or

To enter your password when attempting to perform a start/stop.

## Customizing Colors

Colors are defined inside the script:
- COLOR_PLACEHOLDER must match a color in plex-base.svg.
- The per-state colors are defined under ICON_DEFS.

After changing colors, restart the service to regenerate icons:
```bash
systemctl --user restart plex-appindicator.service
```

You may need to refresh GNOME icons to see the changes.

## Uninstall

Disable autostart:
```bash
systemctl --user disable --now plex-appindicator.service
```

Remove generated icons:
```bash
rm ~/.local/share/icons/hicolor/scalable/status/plex-status-*.svg
```

Remove base icon:
```bash
rm ~/.local/share/icons/plex/plex-base.svg
```

Remove service file:
```bash
rm ~/.config/systemd/user/plex-appindicator.service
systemctl --user daemon-reload
```