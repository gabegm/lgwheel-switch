import asyncio
import os
import re
import shlex

import decky.logger

DRIVER_LGOGWHEELGAMEPAD = "lgogwheelgamepad"
DRIVER_LG4FF = "lg4ff"
LG4FF_GIT_URL = "https://github.com/llmx/lx4ff"

ACTIVE_DRIVER_CHANGED_EVENT = "activeDriverChanged"

# Supported Logitech wheel models
WHEEL_MODELS = {
    "046d:c268": {
        "vendor": "046d",
        "product": "c268",
        "model": "G923 (PS)",
        "modeswitch_cmd": "30f8090701010000",
        "mode": "03",
        "reset": "03",
    },
    "046d:c267": {
        "vendor": "046d",
        "product": "c267",
        "model": "G923 (PS)",
        "modeswitch_cmd": "30f8090701010000",
        "mode": "03",
        "reset": "03",
    },
    "046d:c275": {
        "vendor": "046d",
        "product": "c275",
        "model": "G29",
        "modeswitch_cmd": "30f8090701000000",
        "mode": "03",
        "reset": "03",
    },
    "046d:c292": {
        "vendor": "046d",
        "product": "c292",
        "model": "G920",
        "modeswitch_cmd": "30f8090701000000",
        "mode": "03",
        "reset": "03",
    },
    "046d:c293": {
        "vendor": "046d",
        "product": "c293",
        "model": "G920 (PC)",
        "modeswitch_cmd": "30f8090701000000",
        "mode": "03",
        "reset": "03",
    },
    "046d:c299": {
        "vendor": "046d",
        "product": "c299",
        "model": "G Pro",
        "modeswitch_cmd": "30f8090701000000",
        "mode": "03",
        "reset": "03",
    },
    default: {
        "vendor": "046d",
        "product": "unknown",
        "model": "Unknown Logitech Wheel",
        "modeswitch_cmd": "30f8090701000000",
        "mode": "03",
        "reset": "03",
    },
}


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
        valid_drivers = {DRIVER_LGOGWHEELGAMEPAD, DRIVER_LG4FF}
        if target_driver not in valid_drivers:
            raise ValueError(
                f"Invalid driver '{target_driver}'. Must be one of: {', '.join(sorted(valid_drivers))}"
            )

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

    async def detect_wheel(self):
        """Detect Logitech wheel connected via USB."""
        try:
            # Run lsusb and search for Logitech vendor ID
            process = await asyncio.create_subprocess_exec(
                "lsusb",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return {"detected": False, "error": stderr.decode().strip()}

            output = stdout.decode()
            # Look for Logitech vendor ID (046d)
            for line in output.splitlines():
                if "046d" in line:
                    # Extract vendor:product from the line
                    match = re.search(r"([0-9a-fA-F]{4}):([0-9a-fA-F]{4})", line)
                    if match:
                        vendor = match.group(1).lower()
                        product = match.group(2).lower()
                        key = f"{vendor}:{product}"
                        info = WHEEL_MODELS.get(key, WHEEL_MODELS["default"])
                        info["vendor"] = vendor
                        info["product"] = product
                        info["detected"] = True
                        return info
            
            return {"detected": False, "message": "No Logitech wheel detected"}
        except Exception as e:
            return {"detected": False, "error": str(e)}

    async def check_lg4ff_installed(self):
        """Check if lg4ff is installed and its status."""
        result = {
            "module_loaded": False,
            "dkms_enabled": False,
            "udev_rules_present": False,
        }

        # Check if lg4ff module is loaded
        if os.path.isdir("/sys/module/lx4ff"):
            result["module_loaded"] = True
        elif os.path.isdir("/sys/module/lg4ff"):
            result["module_loaded"] = True

        # Check if DKMS is installed and lg4ff is registered
        try:
            process = await asyncio.create_subprocess_exec(
                "dkms", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, _stderr = await process.communicate()
            if process.returncode == 0:
                # Check if lg4ff is registered with DKMS
                process2 = await asyncio.create_subprocess_exec(
                    "dkms", "status",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process2.communicate()
                if process2.returncode == 0:
                    output = stdout.decode()
                    if "lx4ff" in output or "lg4ff" in output:
                        result["dkms_enabled"] = True
        except Exception as e:
            decky.logger.error(f"Error checking dkms: {e}")

        # Check for udev rules
        udev_rules = [
            "/etc/udev/rules.d/99-lg-wheel.rules",
            "/etc/udev/rules.d/99-lx4ff.rules",
            "/usr/lib/udev/rules.d/99-lg-wheel.rules",
        ]
        for rule_file in udev_rules:
            if os.path.exists(rule_file):
                result["udev_rules_present"] = True
                break

        return result

    async def install_lg4ff(self, wheel_info: dict | None = None):
        """Full install: deps + build lg4ff + create udev rules."""
        steps = []
        errors = []
        read_only_disabled = False

        # --- 1. System dependencies ------------------------------------------------
        try:
            # Verify pacman is available
            p = await asyncio.create_subprocess_exec(
                "pacman", "--version",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append("pacman not found. This plugin requires a Steam Deck or Arch Linux system.")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": False}

            steps.append("1· Disabling read-only mode …")
            p = await asyncio.create_subprocess_exec(
                "steamos-readonly", "disable",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append("Failed to disable read-only mode")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": False}
            read_only_disabled = True
            steps.append("   ✅ read-only disabled")

            steps.append("2· Installing dependencies …")
            pkgs = "usb_modeswitch base-devel git libusb linux-headers".split()
            for pkg in pkgs:
                p = await asyncio.create_subprocess_exec(
                    "sudo", "pacman", "-S", "--noconfirm", pkg,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                await p.communicate()
                if p.returncode != 0:
                    errors.append(f"Failed to install {pkg}")
            steps.append("   ✅ dependencies installed")

            steps.append("3· Re-enabling read-only mode …")
            p = await asyncio.create_subprocess_exec(
                "steamos-readonly", "enable",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            steps.append("   ✅ read-only re-enabled")
        except Exception as exc:
            errors.append(str(exc))
            return {"success": False, "steps": steps, "errors": errors, "requires_reboot": False}

        # --- 2. Build & install lg4ff (lx4ff) ---------------------------------------
        lg4ff_path = "/opt/lg4ff"
        try:
            steps.append("4· Cloning lx4ff repository …")
            p = await asyncio.create_subprocess_exec(
                "git", "clone", LG4FF_GIT_URL, lg4ff_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await p.communicate()
            if p.returncode != 0:
                errors.append(f"Clone failed: {stderr.decode().strip()}")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": False}
            steps.append("   ✅ cloned")

            steps.append("5· Building & installing lx4ff …")

            # Determine the actual DKMS version by reading Makefile
            dkms_version = "1.0"
            makefile_path = os.path.join(lg4ff_path, "Makefile")
            if os.path.isfile(makefile_path):
                try:
                    with open(makefile_path, "r") as f:
                        for line in f:
                            match = re.match(r"^\s*PACKAGE_VERSION\s*[:?]?=\s*(.+)", line)
                            if match:
                                dkms_version = match.group(1).strip()
                                break
                except Exception:
                    pass

            # Run make clean
            p = await asyncio.create_subprocess_exec(
                "sudo", "make", "-C", lg4ff_path, "clean",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append("make clean failed")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

            # Run make
            p = await asyncio.create_subprocess_exec(
                "sudo", "make", "-C", lg4ff_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append("make failed")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

            # Run make install
            p = await asyncio.create_subprocess_exec(
                "sudo", "make", "-C", lg4ff_path, "install",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append("make install failed")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

            # Register with DKMS
            p = await asyncio.create_subprocess_exec(
                "sudo", "dkms", "add", lg4ff_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append("dkms add failed")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

            # Build and install DKMS module with discovered version
            p = await asyncio.create_subprocess_exec(
                "sudo", "dkms", "build", f"lx4ff/{dkms_version}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append(f"dkms build failed (version {dkms_version})")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

            p = await asyncio.create_subprocess_exec(
                "sudo", "dkms", "install", f"lx4ff/{dkms_version}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            if p.returncode != 0:
                errors.append(f"dkms install failed (version {dkms_version})")
                return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

            steps.append(f"   ✅ lx4ff built & DKMS module installed (version {dkms_version})")

            steps.append("6· Creating udev rules …")
            rule_path = "/etc/udev/rules.d/99-lg-wheel.rules"

            # Build the rule content
            if wheel_info and wheel_info.get("detected"):
                v = wheel_info.get("vendor", "046d")
                p_prod = wheel_info.get("product", "c268")
                cmd = wheel_info.get("modeswitch_cmd", "30f8090701000000")
                mode = wheel_info.get("mode", "03")
                reset = wheel_info.get("reset", "03")
                model_name = wheel_info.get("model", "Logitech Wheel")
            else:
                v, p_prod, cmd, mode, reset = "046d", "c268", "30f8090701000000", "03", "03"
                model_name = "Logitech Wheel"

            rule_content = (
                f"## Auto USB mode switch for {model_name}\n"
                f'ACTION=="add", SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{v}", '
                f'ATTRS{{idProduct}}=="{p_prod}", '
                f'ENV{{ID_USB_DRIVER}}!="lx4ff", RUN+="/usr/sbin/modprobe lx4ff"\n'
                f'ACTION=="add", SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{v}", '
                f'ATTRS{{idProduct}}=="{p_prod}", '
                f'ENV{{ID_USB_DRIVER}}=="lx4ff", RUN+="/usr/bin/usb_modeswitch -v {v} -p {p_prod} '
                f'-M {cmd} -m {mode} -r {reset}"\n'
            )
            with open(rule_path, "w") as f:
                f.write(rule_content)
            steps.append("   ✅ udev rules written")

            steps.append("7· Reloading udev rules …")
            p = await asyncio.create_subprocess_exec(
                "sudo", "udevadm", "control", "--reload-rules",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            p = await asyncio.create_subprocess_exec(
                "sudo", "udevadm", "trigger",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await p.communicate()
            steps.append("   ✅ udev rules reloaded")

        except Exception as exc:
            errors.append(str(exc))
            return {"success": False, "steps": steps, "errors": errors, "requires_reboot": True}

        # If there were errors and we disabled read-only, warn the user
        if errors and read_only_disabled:
            errors.insert(0, "⚠️  WARNING: Read-only mode was disabled but installation failed. "
                              "Please run 'sudo steamos-readonly enable' manually to restore system protection.")

        return {"success": True, "steps": steps, "errors": errors, "requires_reboot": True}

    async def build_and_install_lg4ff(self):
        """Clone, build, and install lg4ff with DKMS."""
        result = {
            "steps": [],
            "errors": [],
            "requires_reboot": True,
        }

        lg4ff_path = "/opt/lg4ff"
        
        try:
            # Clone lg4ff repo
            result["steps"].append("📋 Cloning lg4ff repository...")
            process = await asyncio.create_subprocess_exec(
                "git", "clone", LG4FF_GIT_URL, lg4ff_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"Failed to clone lg4ff: {stderr.decode().strip()}")
                return result
            result["steps"].append("✅ lg4ff cloned")
            
            # Build and install
            result["steps"].append("🔨 Building lg4ff...")

            # Determine the actual DKMS version by reading Makefile
            dkms_version = "1.0"
            makefile_path = os.path.join(lg4ff_path, "Makefile")
            if os.path.isfile(makefile_path):
                try:
                    with open(makefile_path, "r") as f:
                        for line in f:
                            match = re.match(r"^\s*PACKAGE_VERSION\s*[:?]?=\s*(.+)", line)
                            if match:
                                dkms_version = match.group(1).strip()
                                break
                except Exception:
                    pass

            # Run make clean
            process = await asyncio.create_subprocess_exec(
                "sudo", "make", "-C", lg4ff_path, "clean",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"make clean failed: {stderr.decode().strip()}")
                return result

            # Run make
            process = await asyncio.create_subprocess_exec(
                "sudo", "make", "-C", lg4ff_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"make failed: {stderr.decode().strip()}")
                return result

            # Run make install
            process = await asyncio.create_subprocess_exec(
                "sudo", "make", "-C", lg4ff_path, "install",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"make install failed: {stderr.decode().strip()}")
                return result

            # Register with DKMS
            process = await asyncio.create_subprocess_exec(
                "sudo", "dkms", "add", lg4ff_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"dkms add failed: {stderr.decode().strip()}")
                return result

            # Build DKMS module with discovered version
            process = await asyncio.create_subprocess_exec(
                "sudo", "dkms", "build", f"lx4ff/{dkms_version}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"dkms build failed: {stderr.decode().strip()}")
                return result

            # Install DKMS module
            process = await asyncio.create_subprocess_exec(
                "sudo", "dkms", "install", f"lx4ff/{dkms_version}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                result["errors"].append(f"dkms install failed: {stderr.decode().strip()}")
                return result

            result["steps"].append(f"✅ lg4ff built and DKMS module installed (version {dkms_version})")
            
            # Create lg4ff udev rule using detected wheel info
            result["steps"].append("📝 Creating udev rules for lg4ff...")
            udev_path = "/etc/udev/rules.d/99-lx4ff.rules"

            # Try to find matching wheel model for proper parameters
            wheel_params = None
            for key, info in WHEEL_MODELS.items():
                if key != "default":
                    # Check if vendor matches any detected wheel
                    if info["vendor"] == "046d":
                        wheel_params = info
                        break

            if wheel_params:
                udev_content = (
                    f"# LG4FF udev rules for {wheel_params['model']}\n"
                    f'ACTION=="add", SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{wheel_params["vendor"]}", '
                    f'ATTRS{{idProduct}}=="{wheel_params["product"]}", '
                    f'ENV{{ID_USB_DRIVER}}!="lx4ff", '
                    f'RUN+="/usr/sbin/modprobe lx4ff"\n'
                    f'ACTION=="add", SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{wheel_params["vendor"]}", '
                    f'ATTRS{{idProduct}}=="{wheel_params["product"]}", '
                    f'ENV{{ID_USB_DRIVER}}="lx4ff", '
                    f'RUN+="/usr/bin/usb_modeswitch -v {wheel_params["vendor"]} -p {wheel_params["product"]} '
                    f'-M {wheel_params["modeswitch_cmd"]} -m {wheel_params["mode"]} -r {wheel_params["reset"]}"\n'
                )
            else:
                # Fallback: generic rule for any Logitech device
                udev_content = (
                    "# LG4FF udev rules\n"
                    'ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="046d", '
                    'ENV{ID_USB_DRIVER}!="lx4ff", '
                    'RUN+="/usr/sbin/modprobe lx4ff"\n'
                )

            with open(udev_path, "w") as f:
                f.write(udev_content)
            result["steps"].append("✅ lg4ff udev rules created")
            
            # Reload udev rules
            result["steps"].append("🔄 Reloading udev rules...")
            process = await asyncio.create_subprocess_exec(
                "sudo", "udevadm", "control", "--reload-rules",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, _stderr = await process.communicate()
            result["steps"].append("✅ udev rules reloaded")
            
            return result
        except Exception as e:
            result["errors"].append(str(e))
            return result

    async def configure_udev_rules(self, wheel_info):
        """Configure udev rules for auto-switching USB mode."""
        result = {
            "success": False,
            "errors": [],
            "step": "",
        }
        
        if not wheel_info or not wheel_info.get("detected"):
            result["errors"].append("No wheel detected. Please connect your Logitech wheel first.")
            return result
        
        vendor = wheel_info["vendor"]
        product = wheel_info["product"]
        cmd = wheel_info["modeswitch_cmd"]
        mode = wheel_info["mode"]
        reset = wheel_info["reset"]
        
        rule_content = (
            f"## Auto USB mode switch for {shlex.quote(wheel_info.get('model', 'Logitech wheel'))}\n"
            f'ACTION=="add", SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{shlex.quote(vendor)}", '
            f'ATTRS{{idProduct}}=="{shlex.quote(product)}", '
            f'RUN+="/usr/bin/usb_modeswitch -v {shlex.quote(vendor)} -p {shlex.quote(product)} '
            f'-M {shlex.quote(cmd)} -m {shlex.quote(mode)} -r {shlex.quote(reset)}"\n'
        )
        
        rule_path = "/etc/udev/rules.d/99-lg-wheel.rules"
        
        try:
            with open(rule_path, "w") as f:
                f.write(rule_content)
            
            # Reload udev rules
            process = await asyncio.create_subprocess_exec(
                "udevadm", "control", "--reload-rules",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, _stderr = await process.communicate()
            
            result["success"] = True
            result["step"] = f"✅ udev rule created for {wheel_info.get('model', 'Logitech wheel')}"
        except Exception as e:
            result["errors"].append(str(e))
        
        return result

    async def get_install_instructions(self, model_name: str = None):
        """
        Get installation instructions for lg4ff.
        These should be copied to clipboard and pasted into konsole.
        """
        if model_name:
            # Look up wheel info for the specific model
            model_info = None
            for key, info in WHEEL_MODELS.items():
                if info.get("model") == model_name:
                    model_info = info
                    break
            if not model_info:
                model_info = WHEEL_MODELS["default"]
        else:
            model_info = WHEEL_MODELS["default"]
        
        vendor = model_info["vendor"]
        product = model_info["product"]
        cmd = model_info["modeswitch_cmd"]
        mode = model_info["mode"]
        reset = model_info.get("reset", "03")
        
        instructions = f"""
=== LG4FF Installation Instructions for {shlex.quote(model_info.get('model', 'Logitech wheel'))} ===

Step 1: Set password and disable read-only mode (requires sudo)
  passwd
  sudo steamos-readonly disable

Step 2: Update packages
  sudo pacman -Syu

Step 3: Install lg4ff (requires yay or manual build):
  # Option A: Using yay (recommended)
  sudo pacman -S yay
  yay -S new-lg4ff-git

  # Option B: Manual build
  sudo pacman -S --noconfirm base-devel git linux-headers libusb
  mkdir -p /opt && cd /opt
  git clone https://github.com/llmx/lx4ff.git
  cd lx4ff
  sudo make
  sudo make install
  sudo dkms add .
  sudo dkms build lx4ff/1.0
  sudo dkms install lx4ff/1.0

Step 4: Create udev rule for automatic USB mode switching
  sudo bash -c "cat > /etc/udev/rules.d/99-lg-wheel.rules << 'EOF'
## Auto USB mode switch for {shlex.quote(model_info.get('model', 'Logitech wheel'))}
ACTION==\"add\", SUBSYSTEM==\"usb\", ATTRS{{idVendor}}==\"{shlex.quote(vendor)}\",
ATTRS{{idProduct}}==\"{shlex.quote(product)}\", RUN+=\"/usr/bin/usb_modeswitch -v {shlex.quote(vendor)} -p {shlex.quote(product)}
-M {shlex.quote(cmd)} -m {shlex.quote(mode)} -r {shlex.quote(reset)}\"
EOF"

Step 5: Reload udev rules and reboot
  sudo udevadm control --reload-rules
  sudo udevadm trigger

Step 6: Re-enable read-only mode
  sudo steamos-readonly enable

IMPORTANT: A reboot is required for the DKMS module to load.
"""
        return instructions