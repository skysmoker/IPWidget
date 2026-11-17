# IPWidget

**English** | [Русский](README.ru.md)

A lightweight, minimalist Windows desktop widget built with Python and PyQt6 that displays your current public IP address, country flag, city, and connection status right on your screen.

## Features

- **Real-time IP & Geolocation:** Displays your public IPv4 address, country flag, ISO3 country code, and city using multiple fallback APIs (`ipwho.is`, `ip-api.com`, `geojs.io`, `ipinfo.io`).
- **Detailed Hover Card:** Hover over the widget for 1 second to view your ISP, active network interface with local IP, IPv6 address (if available), API ping latency, and timezone.
- **Privacy Mode:** Optionally mask your IP address (`•••.•••`) until you hover over the widget.
- **Smart Positioning & Themes:** Snap to any screen corner or drag freely anywhere with `Middle Mouse Button` or `Alt + Left Click`. Supports Dark, Light, and automatic Windows system themes, plus adjustable opacity and scale (75%–150%).
- **Low Resource Usage (AFK Pause):** Automatically pauses background polling after 5 minutes of user inactivity and resumes instantly upon activity, wake from sleep, or screen unlock.
- **Fullscreen Auto-Hide:** Automatically hides when another application runs in fullscreen mode (games, videos, presentations).
- **Bilingual Interface (EN / RU):** Automatically detects your Windows UI language on first launch, with instant switching between English and Russian in Settings.
- **Built-in Auto-Updater:** Checks GitHub Releases for new versions and updates the standalone `.exe` seamlessly.

## Quick Start

### Standalone Executable (Windows)
1. Download the latest `IPWidget.exe` from the [Releases](https://github.com/skysmoker/IPWidget/releases/latest) page.
2. Run `IPWidget.exe` (no installation required).
3. **Left-click** the widget to copy your IPv4 address; **Right-click** to open Settings.

### Run from Source
1. Clone the repository: `git clone https://github.com/skysmoker/IPWidget.git`
2. Open the folder: `cd IPWidget`
3. Create and activate a virtual environment: `python -m venv venv` and `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the widget: `python main.py`

## Author & License

Created by [Ivan Cherkez (@SkySmoker)](https://t.me/SkySmoker). Distributed under the MIT License.