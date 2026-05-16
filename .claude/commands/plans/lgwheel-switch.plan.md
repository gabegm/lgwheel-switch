# LG Wheel Switch - Steam Deck Plugin Plan

## Overview
A Decky frontend plugin to toggle between `lgogwheelgamepad` and `lg4ff` kernel drivers for Logitech racing wheels on Steam Deck.

## Files to Create

### Root Directory
1. **plugin.json** - Plugin metadata (name, author, flags, publish info)
2. **package.json** - Node.js dependencies (@decky/ui, @decky/api, rollup, typescript)
3. **tsconfig.json** - TypeScript config (ES2020, react-jsx, strict mode)
4. **rollup.config.js** - Rollup bundler config using @decky/rollup
5. **LICENSE** - BSD 3-Clause license (with original template attribution)
6. **README.md** - Plugin documentation
7. **py_modules/.keep** - Placeholder for Python module
8. **defaults/.keep** - Placeholder for defaults directory

### Frontend (src/)
9. **src/types.d.ts** - SVG/PNG/JPG module declarations
10. **src/index.tsx** - Main React component with toggle button UI

### Backend (py_modules/)
11. **py_modules/main.py** - Python class with plugin backend
    - `toggle_drivers()` - Switch between lgogwheelgamepad and lg4ff
    - `_main()` - Init: detect current driver, emit state to frontend
    - `_unload()` - Cleanup

## Architecture

### Frontend (Index.tsx)
- Toggle button: "Switch to lgogwheelgamepad" / "Switch to lg4ff"
- Status indicator showing current active driver
- Error display for failed driver switches
- Calls backend callable via @decky/api

### Backend (main.py)
- Uses subprocess.run() to execute:
  - `rmmod lgogwheelgamepad` or `rmmod lg4ff` to unload current driver
  - `modprobe <target_driver>` to load target driver
  - `pactl reload-module` to refresh audio routing (lgogwheelgamepad specific)
- Handles errors: checks if drivers exist, if they're in use, etc.
- Uses asyncio for non-blocking calls

### Plugin Flow
1. Load → detect which driver is currently loaded → emit state to frontend
2. User clicks toggle → call backend with target driver
3. Backend unloads current, loads target, emits updated state
4. Frontend updates UI accordingly

## Key Behaviors
- Auto-detect current driver on load using: `lsmod | grep ...` or `ls /sys/module/`
- If no driver loaded → default to `lgogwheelgamepad`
- Driver detection via checking `/sys/module/lgogwheelgamepad` or `/sys/module/lg4ff` existence
- Log all operations via `decky.logger`
