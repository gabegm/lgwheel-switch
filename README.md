# LG Wheel Switch

A Steam Deck plugin to switch between `lgogwheelgamepad` and `lg4ff` kernel drivers for Logitech racing wheels.

## Overview

This plugin allows you to toggle between two kernel drivers used for Logitech racing wheels on Steam Deck:

- **lgogwheelgamepad** — Default GOG-compatible driver that provides haptic feedback in games
- **lg4ff** — Logitech 4 Force Feedback driver with advanced force feedback support

## Installation

1. Ensure the LG Wheel Switch plugin is downloaded to your Decky loader
2. Open the plugin menu in Steam (Shift+Tab)
3. The plugin will appear in the sidebar and auto-detect the currently active driver on load

## Usage

1. Open the sidebar in Steam (Shift+Tab)
2. Click on **LG Wheel Switch** in the plugin list
3. Click the toggle button to switch drivers
4. Wait for the switch to complete — the UI will update with the new active driver

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
