# IPWidget

**English** | [Русский](README.ru.md)

A lightweight, minimalist Windows desktop widget built with Python and PyQt6 that displays your current public IP address, country flag, city, and connection status right on your screen.

<table align="center">
  <tr>
    <td rowspan="2" align="center" valign="middle">
      <img width="364" height="512" alt="screen-05" src="https://github.com/user-attachments/assets/4b7072a7-0d2f-49a7-a696-7634dd2fa72f" />
    </td>
    <td align="center" valign="middle">
      <img width="145" height="54" alt="screen-01" src="https://github.com/user-attachments/assets/51f629e0-f654-4cf0-98e3-1bd3da01566c" />
      &nbsp;
      <img width="205" height="54" alt="screen-02" src="https://github.com/user-attachments/assets/4160ab00-a502-4593-91eb-f7de67600783" />
      &nbsp;
      <img width="152" height="54" alt="screen-03" src="https://github.com/user-attachments/assets/fde9bf83-6a7e-4293-9e17-40963c21b8e7" />
      &nbsp;
    </td>
  </tr>
  <tr>
    <td align="center" valign="middle">
      <img width="183" height="153" alt="screen-07" src="https://github.com/user-attachments/assets/809a95ac-1792-450c-97b5-cc751086b24e" />
    </td>
  </tr>
</table>

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
