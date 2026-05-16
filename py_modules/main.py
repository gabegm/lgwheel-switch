import asyncio
import os

import decky.logger

DRIVER_LGOGWHEELGAMEPAD = "lgogwheelgamepad"
DRIVER_LG4FF = "lg4ff"

ACTIVE_DRIVER_CHANGED_EVENT = "activeDriverChanged"


class Plugin:
    def __init__(self):
        self._closed = False

    async def init(self) -> None:
        self.plugin_api = await self.plugin_api_factory()
        decky.logger.info("LG Wheel Switch plugin initialized")

    async def _main(self) -> str:
        current = self._detect_current_driver()
        decky.logger.info(f"Active driver detected: {current}")
        self._emit(current)
        return current

    async def _unload(self) -> None:
        decky.logger.info("LG Wheel Switch plugin unloaded")
        self._closed = True

    async def toggle_drivers(self, target_driver: str) -> str:
        current = self._detect_current_driver()
        if current == target_driver:
            decky.logger.info(f"Target driver {target_driver} is already active")
            return target_driver

        decky.logger.info(f"Switching from {current} to {target_driver}")

        await self._unload_driver(current)
        await self._load_driver(target_driver)

        new_current = self._detect_current_driver() or target_driver
        decky.logger.info(f"Switch complete. Active driver is now: {new_current}")

        self._emit(new_current)
        return new_current

    def detect_current_driver(self) -> str | None:
        return self._detect_current_driver()

    def _detect_current_driver(self) -> str | None:
        if os.path.isdir(f"/sys/module/{DRIVER_LGOGWHEELGAMEPAD}"):
            return DRIVER_LGOGWHEELGAMEPAD
        if os.path.isdir(f"/sys/module/{DRIVER_LG4FF}"):
            return DRIVER_LG4FF
        return None

    def _emit(self, data: str | None) -> None:
        if not self._closed:
            self.plugin_api.send_event_to_client(ACTIVE_DRIVER_CHANGED_EVENT, data)

    async def _unload_driver(self, driver: str) -> None:
        if not driver:
            return
        process = await asyncio.create_subprocess_exec(
            "rmmod",
            driver,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            msg = stderr.decode().strip()
            decky.logger.error(f"Failed to unload {driver}: {msg}")
            raise RuntimeError(f"Failed to unload {driver}: {msg}")
        decky.logger.info(f"Unloaded {driver}")

    async def _load_driver(self, driver: str) -> None:
        process = await asyncio.create_subprocess_exec(
            "modprobe",
            driver,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            msg = stderr.decode().strip()
            decky.logger.error(f"Failed to load {driver}: {msg}")
            raise RuntimeError(f"Failed to load {driver}: {msg}")
        decky.logger.info(f"Loaded {driver}")
