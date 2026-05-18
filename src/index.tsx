import {
  Button,
  PanelSection,
  PanelSectionRow,
  Spinner,
  Collapsible,
  TextArea,
} from "@decky/ui";
import { useState, useEffect, useCallback } from "react";
import {
  call,
  callable,
  addEventListener,
  definePlugin,
} from "@decky/api";

const ACTIVE_DRIVER_CHANGED_EVENT = "activeDriverChanged";
const DRV_LGOG = "lgogwheelgamepad";
const DRV_LG4FF = "lg4ff";

const toggleDrivers = callable<[string]>("toggle_drivers");
const checkLg4ffInstalled = callable<[], any>("check_lg4ff_installed");
const detectWheel = callable<[], any>("detect_wheel");
const installLg4ff = callable<[], any>("install_lg4ff");
const configureUdevRules = callable<[any], any>("configure_udev_rules");
const getInstallInstructions = callable<[string], string>("get_install_instructions");
const copyToClipboard = async (text: string) => {
  await navigator.clipboard.writeText(text);
};

function LGWheelSwitchPlugin() {
  const [activeDriver, setActiveDriver] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wheelInfo, setWheelInfo] = useState<any>(null);
  const [lg4ffStatus, setLg4ffStatus] = useState<any>(null);
  const [installStatus, setInstallStatus] = useState<any>(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [installInstructions, setInstallInstructions] = useState("");
  const [copied, setCopied] = useState(false);

  // Detect wheel on plugin mount
  const detectAndSetWheel = useCallback(async () => {
    try {
      const wheel = await detectWheel();
      setWheelInfo(wheel);
    } catch (e) {
      console.error("detect_wheel failed:", e);
    }
  }, []);

  // Check lg4ff status on plugin mount
  const checkLg4ff = useCallback(async () => {
    try {
      const status = await checkLg4ffInstalled();
      setLg4ffStatus(status);
    } catch (e) {
      console.error("check_lg4ff_installed failed:", e);
    }
  }, []);

  const detectAndSetDriver = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const detected = await call<[], string | null>("detect_current_driver");
      if (detected !== undefined && detected !== null) {
        setActiveDriver(detected);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    detectAndSetDriver();
    detectAndSetWheel();
    checkLg4ff();
    const handler = (data: string | null) => {
      setActiveDriver(data);
    };
    addEventListener<[string | null]>(
      ACTIVE_DRIVER_CHANGED_EVENT,
      handler
    );
    return () => {
      addEventListener<[string | null]>(
        ACTIVE_DRIVER_CHANGED_EVENT,
        handler
      );
    };
  }, [detectAndSetDriver, detectAndSetWheel, checkLg4ff]);

  const targetDriver = activeDriver === DRV_LGOG ? DRV_LG4FF : DRV_LGOG;
  const isLoading = loading || activeDriver === null;
  const buttonLabel = isLoading
    ? "Detecting driver..."
    : `Switch to ${targetDriver}`;

  const handleToggle = useCallback(async () => {
    if (isLoading) return;
    setError(null);
    try {
      await toggleDrivers(targetDriver);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error("toggle_drivers failed:", msg);
      setError(msg);
    }
  }, [isLoading, targetDriver]);

  const handleSwitchToDriver = useCallback(
    async (drv: string) => {
      setError(null);
      try {
        await toggleDrivers(drv);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        console.error("toggle_drivers failed:", msg);
        setError(msg);
      }
    },
    []
  );

  const switchToLG4FF = useCallback(() => {
    handleSwitchToDriver(DRV_LG4FF);
  }, [handleSwitchToDriver]);

  const switchToLGOGWheelGamepad = useCallback(() => {
    handleSwitchToDriver(DRV_LGOG);
  }, [handleSwitchToDriver]);

  const handleCopyInstructions = useCallback(async () => {
    try {
      const model = wheelInfo?.model || lg4ffStatus?.model || "Unknown";
      const instructions = await getInstallInstructions(model);
      setInstallInstructions(instructions);
      setShowInstructions(true);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("get_install_instructions failed:", e);
    }
  }, [wheelInfo, lg4ffStatus]);

  const handleInstallLg4ff = useCallback(async () => {
    setError(null);
    setInstallStatus(null);
    try {
      const result = await installLg4ff();
      setInstallStatus(result);
      if (result.success) {
        // Refresh status
        checkLg4ff();
      } else {
        setError("Installation failed. See details below.");
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error("install_lg4ff failed:", msg);
      setError(msg);
    }
  }, [checkLg4ff]);

  const handleConfigureUdev = useCallback(async () => {
    if (!wheelInfo || !wheelInfo.detected) {
      setError("No wheel detected. Please connect your Logitech wheel first.");
      return;
    }
    setError(null);
    try {
      const result = await configureUdevRules(wheelInfo);
      if (result.success) {
        checkLg4ff();
      } else {
        setError("Failed to configure udev rules.");
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error("configure_udev_rules failed:", msg);
      setError(msg);
    }
  }, [wheelInfo, checkLg4ff]);

  const lg4ffNotInstalled = !lg4ffStatus?.moduleLoaded && !lg4ffStatus?.dkmsEnabled;

  return {
    name: "LG Wheel Switch",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="currentColor"
        style={{ marginRight: "8px" }}
      >
        <path d="M8 4.7a3.3 3.3 0 1 1 0 6.6 3.3 3.3 0 0 1 0-6.6zm0 1a2.3 2.3 0 1 0 0 4.6 2.3 2.3 0 0 0 0-4.6zM8 0a.8.8 0 0 1 .8.8v1.4a.8.8 0 0 1-1.6 0V.8A.8.8 0 0 1 8 0zm0 14.8a.8.8 0 0 1 .8.8v1.4a.8.8 0 0 1-1.6 0v-1.4a.8.8 0 0 1 .8-.8zM15.2 8a.8.8 0 0 1-.8.8h-1.4a.8.8 0 0 1 0-1.6h1.4a.8.8 0 0 1 .8.8zM2.2 8a.8.8 0 0 1-.8.8H0a.8.8 0 0 1 0-1.6h1.4a.8.8 0 0 1 .8.8zm13.07-5.29a.8.8 0 0 1 0 1.13l-1 1a.8.8 0 0 1-1.13-1.13l1-1a.8.8 0 0 1 1.13 0zM3.83 11.47a.8.8 0 0 1 0 1.13l-1 1a.8.8 0 0 1-1.13-1.13l1-1a.8.8 0 0 1 1.13 0zm10.14 3.54a.8.8 0 0 1-1.13 0l-1-1a.8.8 0 1 1 1.13-1.13l1 1a.8.8 0 0 1 0 1.13zM2.93 1.93a.8.8 0 0 1-1.13 0l-1-1a.8.8 0 0 1 1.13-1.13l1 1a.8.8 0 0 1 0 1.13z" />
      </svg>
    ),
    content: (
      <PanelSection title="LG Wheel Switch">
        {/* Wheel Detection */}
        <PanelSectionRow>
          <div>
            Wheel: {wheelInfo?.model ? `${wheelInfo.model} (${wheelInfo.vendor}:${wheelInfo.product})` : "—"}
          </div>
        </PanelSectionRow>

        {/* lg4ff Status */}
        <PanelSectionRow>
          <div>
            lg4ff: {lg4ffStatus?.moduleLoaded ? "✅ Installed" : lg4ffStatus?.dkmsEnabled ? "✅ DKMS Installed" : "❌ Not installed"}
          </div>
        </PanelSectionRow>

        {/* Current Driver */}
        <PanelSectionRow>
          <div>
            Current driver: {activeDriver ?? "—"}
          </div>
        </PanelSectionRow>

        {isLoading && (
          <PanelSectionRow>
            <Spinner />
          </PanelSectionRow>
        )}
        
        {error && (
          <PanelSectionRow>
            <div style={{ color: "red", textAlign: "center", width: "100%" }}>
              Error: {error}
            </div>
          </PanelSectionRow>
        )}

        {/* Driver Toggle */}
        <PanelSectionRow>
          <Button onClick={handleToggle} disabled={isLoading}>
            {buttonLabel}
          </Button>
        </PanelSectionRow>
        
        {/* Switch to lgogwheelgamepad */}
        <PanelSectionRow>
          <Button
            onClick={switchToLGOGWheelGamepad}
            disabled={activeDriver === DRV_LGOG}
          >
            Switch to lgogwheelgamepad
          </Button>
        </PanelSectionRow>

        {/* lg4ff Installation Section */}
        {lg4ffNotInstalled && (
          <PanelSection title="lg4ff Installation">
            <PanelSectionRow>
              <div style={{ color: "red" }}>
                lg4ff driver is not installed. Please install it first before switching.
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <Collapsible title="Show manual install instructions">
                <div style={{ marginBottom: "16px" }}>
                  <Button onClick={handleCopyInstructions}>
                    Copy Instructions to Clipboard
                  </Button>
                </div>
                <TextArea value={installInstructions} style={{ width: "100%", height: "200px", resize: "none" }} readOnly />
              </Collapsible>
            </PanelSectionRow>
            <PanelSectionRow>
              <Button onClick={handleInstallLg4ff}>
                Auto Install lg4ff
              </Button>
            </PanelSectionRow>
            
            {/* Installation progress/error */}
            {installStatus && (
              <PanelSectionRow>
                <div style={{ color: installStatus.success ? "green" : "red" }}>
                  {installStatus.success ? "✅ Installation successful!" : "❌ Installation failed"}
                  {installStatus.require_reboot && (
                    <div style={{ marginTop: "8px" }}>
                      ⚠️ A reboot is now required for the DKMS module to load.
                    </div>
                  )}
                </div>
              </PanelSectionRow>
            )}
          </PanelSection>
        )}

        {/* Configure USB Mode Switch */}
        <PanelSection title="USB Mode Switch">
          <PanelSectionRow>
            {wheelInfo?.detected ? (
              <div>
                Wheel detected: {wheelInfo.model}
              </div>
            ) : (
              <div style={{ color: "red" }}>
                No wheel detected. Connect your Logitech wheel first.
              </div>
            )}
          </PanelSectionRow>
          <PanelSectionRow>
            <Button onClick={handleConfigureUdev} disabled={!wheelInfo?.detected}>
              Configure USB Mode Switch via udev
            </Button>
          </PanelSectionRow>
        </PanelSection>

        {/* Open Konsole Button */}
        <PanelSection title="Open Konsole">
          <PanelSectionRow>
            <Button onClick={() => alert("To open konsole, press Steam + X on your Steam Deck")}>
              Open Konsole
            </Button>
          </PanelSectionRow>
        </PanelSection>
      </PanelSection>
    ),
  };
}

export default definePlugin(LGWheelSwitchPlugin);
