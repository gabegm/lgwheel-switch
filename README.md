# LG Wheel Switch

> **⚠️ DANGER — USE AT YOUR OWN RISK**
>
> **This plugin is under heavy development and is NOT ready for production use.**
> It modifies kernel modules, disables system read-only protection, installs DKMS drivers, and modifies udev rules.
> **Incorrect use can render your Steam Deck unbootable or permanently damage your hardware.**
>
> **By using this plugin you agree that:**
> - The author takes **no responsibility** for any damage, data loss, or hardware issues resulting from its use.
> - You are solely responsible for backing up your system and understanding what each action does.
> - You should only use this plugin if you are comfortable recovering a broken Steam Deck from a USB recovery image.
> - This software is provided "AS IS" without warranty of any kind, express or implied.

A Steam Deck plugin to switch between `lgogwheelgamepad` and `lg4ff` kernel drivers for Logitech racing wheels.

## Overview

This plugin allows you to toggle between two kernel drivers used for Logitech racing wheels on Steam Deck:

- **lgogwheelgamepad** — Default GOG-compatible driver that provides haptic feedback in games
- **lg4ff** — Logitech 4 Force Feedback driver with advanced force feedback support

## Features

- **Auto-detect** connected Logitech racing wheel and display model/vendor info
- **Toggle** between `lgogwheelgamepad` and `lg4ff` drivers with one click
- **Auto-install** lg4ff driver (via AUR helper) or show manual install instructions
- **Configure udev rules** automatically for correct USB mode switching
- **Real-time status** display for driver, wheel detection, and lg4ff module
- **Open Konsole** quick access via the plugin

## Installation

1. Ensure the LG Wheel Switch plugin is downloaded to your Decky loader
2. Open the plugin menu in Steam (Shift+Tab)
3. The plugin will appear in the sidebar

## Usage

### Switching Drivers

1. Open the sidebar in Steam (Shift+Tab)
2. Click on **LG Wheel Switch** in the plugin list
3. The plugin auto-detects your wheel and current driver
4. Click the toggle button to switch drivers
5. Wait for the switch to complete — the UI updates with the new active driver

### Installing lg4ff

If lg4ff is not installed, you'll see two options:

1. **Auto Install lg4ff** — Automatically installs via AUR helper (requires `yay` or `pikaur`)
2. **Manual install instructions** — Shows copy-paste commands if auto-install isn't available or fails

### Configuring USB Mode Switch

1. Connect your Logitech wheel (turn the wheel on)
2. Click **Configure USB Mode Switch via udev**
3. The plugin detects the wheel and creates/updates the udev rule

## Plugin UI

The plugin displays:
- **Wheel**: Model name, vendor ID, and product ID (when detected)
- **lg4ff**: Installation status (module loaded or DKMS enabled)
- **Current driver**: Active kernel driver name
- **Driver switch**: Toggle button + direct switch buttons
- **lg4ff installation**: Auto or manual install options
- **USB Mode Switch**: udev rule configuration
- **Open Konsole**: Quick access to terminal

## Driver Information

### lgogwheelgamepad

The default driver for Logitech wheels on Steam Deck. Provides basic force feedback and works with GOG games. Haptic feedback is supported for compatible titles.

### lg4ff

A specialized force feedback driver for Logitech devices. Offers advanced force feedback features including custom force profiles and detailed wheel configuration. Requires `linux-gpust` utilities for full customization.

## FAQ

**Q: Which driver should I use?**
A: Use `lgogwheelgamepad` for general gaming. Switch to `lg4ff` if you need advanced force feedback features or custom wheel configuration.

**Q: Will switching drivers disconnect my wheel?**
A: Briefly. During the switch the wheel will disconnect and reconnect. Give it a moment after clicking toggle.

**Q: How do I know which driver is currently active?**
A: The plugin displays the active driver name on the toggle screen. It auto-detects on load.

**Q: Can I use both drivers at the same time?**
A: No, only one driver can be active at a time. The plugin automatically unloads the current driver before loading the target.

**Q: What happens if I close the plugin while switching?**
A: The switch will continue in the background. The active driver will be detected on next reload.

**Q: How do I install lg4ff?**
A: Use the **Auto Install lg4ff** button in the plugin, or copy the manual instructions and run them in konsole.

**Q: The plugin says "No wheel detected". What should I do?**
A: Make sure your Logitech wheel is connected and powered on. Wait a few seconds and the plugin will try again.

**Q: What are udev rules and why do I need them?**
A: udev rules tell Linux how to handle USB devices. They ensure the correct kernel module is linked to your wheel when you switch modes.
