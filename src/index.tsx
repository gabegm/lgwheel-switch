import {
  Button,
  PanelSection,
  PanelSectionRow,
  Spinner,
} from "@decky/ui";
import { useState, useEffect, useCallback } from "react";
import {
  call,
  callable,
  addEventListener,
  definePlugin,
} from "@decky/api";

const ACTIVE_DRIVER_CHANGED_EVENT = "activeDriverChanged";
const DRV_LSOG = "lgogwheelgamepad";
const DRV_LG4FF = "lg4ff";

const toggleDrivers = callable<[string]>("toggle_drivers");

function LGWheelSwitchPlugin() {
  const [activeDriver, setActiveDriver] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    const handler = (data: string | null) => {
      setActiveDriver(data);
    };
    addEventListener<[string | null]>(
      ACTIVE_DRIVER_CHANGED_EVENT,
      handler
    );
  }, [detectAndSetDriver]);

  const targetDriver = activeDriver === DRV_LSOG ? DRV_LG4FF : DRV_LSOG;
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
    handleSwitchToDriver(DRV_LSOG);
  }, [handleSwitchToDriver]);

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
        <PanelSectionRow>
          <div>Current driver: {activeDriver ?? "—"}</div>
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
        <PanelSectionRow>
          <Button onClick={handleToggle} disabled={isLoading}>
            {buttonLabel}
          </Button>
        </PanelSectionRow>
        <PanelSectionRow>
          <Button
            onClick={switchToLG4FF}
            disabled={activeDriver === DRV_LG4FF}
          >
            Switch to lg4ff
          </Button>
        </PanelSectionRow>
        <PanelSectionRow>
          <Button
            onClick={switchToLGOGWheelGamepad}
            disabled={activeDriver === DRV_LSOG}
          >
            Switch to lgogwheelgamepad
          </Button>
        </PanelSectionRow>
      </PanelSection>
    ),
  };
}

export default definePlugin(LGWheelSwitchPlugin);
