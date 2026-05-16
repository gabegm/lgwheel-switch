import asyncio
import os
import re

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

    async def install_dependencies(self):
        """Install dependencies (usb_modeswitch, base development tools)."""
        deps = []
        errors = []
        
        try:
            # Disable read-only mode warning
            deps.append("⚠️  Step 1: Disabling read-only mode...")
            process = await asyncio.create_subprocess_exec(
                "steamos-readonly", "disable",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, stderr = await process.communicate()
            if process.returncode != 0:
                errors.append(f"Failed to disable read-only mode: {stderr.decode().strip()}")
            else:
                deps.append("✅ Read-only mode disabled")
            
            # Install usb_modeswitch
            deps.append("📦 Step 2: Installing usb_modeswitch...")
            process = await asyncio.create_subprocess_exec(
                "sudo", "pacman", "-S", "--noconfirm", "usb_modeswitch",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                errors.append(f"Failed to install usb_modeswitch: {stderr.decode().strip()}")
            else:
                deps.append("✅ usb_modeswitch installed")
            
            # Install base dependencies
            deps.append("📦 Step 3: Installing development dependencies...")
            packages = ["base-devel", "git", "libusb", "linux-headers"]
            pkg_list = " ".join(packages)
            process = await asyncio.create_subprocess_exec(
                "sudo", "pacman", "-S", "--noconfirm", pkg_list,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                errors.append(f"Failed to install dev tools: {stderr.decode().strip()}")
            else:
                deps.append("✅ Development tools installed")
            
            # Re-enable read-only
            deps.append("🔒 Step 4: Re-enabling read-only mode...")
            process = await asyncio.create_subprocess_exec(
                "steamos-readonly", "enable",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, _stderr = await process.communicate()
            deps.append("✅ Read-only mode re-enabled")

        except Exception as e:
            errors.append(str(e))
        
        return {"deps_installed": deps, "errors": errors}

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
            chdir_process = await asyncio.create_subprocess_exec(
                "sudo", "--", "bash", "-c",
                f"cd {lg4ff_path} && make clean && make && sudo make install && sudo dkms add . && sudo dkms build lx4ff/1.0 && sudo dkms install lx4ff/1.0"
            )
            stdout, stderr = await chdir_process.communicate()
            if chdir_process.returncode != 0:
                result["errors"].append(f"Build failed: {stderr.decode().strip()}")
                return result
            result["steps"].append("✅ lg4ff built and DKMS module installed")
            
            # Create lg4ff udev rule
            result["steps"].append("📝 Creating udev rules for lg4ff...")
            udev_path = "/etc/udev/rules.d/99-lx4ff.rules"
            udev_content = (
                "# LG4FF udev rules\n"
                "ACTION==\"add\", SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"046d\", "
                "ENV{ID_USB_DRIVER}!=\"lx4ff\", RUN+=\"/usr/sbin/modprobe lx4ff\"\n"
                "ACTION==\"add\", SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"046d\", "
                "ENV{ID_USB_DRIVER}=\"lx4ff\", RUN+=\"/usr/bin/usb_modeswitch -v 046d -p %k -M 30f8090701010000 -m 03 -r 03\"\n"
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
            f"## Auto USB mode switch for {wheel_info.get('model', 'Logitech wheel')}\n"
            f'ACTION=="add", SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{vendor}", '
            f'ATTRS{{idProduct}}=="{product}", RUN+="/usr/bin/usb_modeswitch -v {vendor} -p {product} '
            f'-M {cmd} -m {mode} -r {reset}"\n'
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
=== LG4FF Installation Instructions for {model_info.get('model', 'Logitech wheel')} ===

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
## Auto USB mode switch for {model_info.get('model', 'Logitech wheel')}
ACTION==\"add\", SUBSYSTEM==\"usb\", ATTRS{{idVendor}}==\"{vendor}\", 
ATTRS{{idProduct}}==\"{product}\", RUN+=\"/usr/bin/usb_modeswitch -v {vendor} -p {product} 
-M {cmd} -m {mode} -r {reset}\"
EOF"

Step 5: Reload udev rules and reboot
  sudo udevadm control --reload-rules
  sudo udevadm trigger

Step 6: Re-enable read-only mode
  sudo steamos-readonly enable

IMPORTANT: A reboot is required for the DKMS module to load.
"""
        return instructions