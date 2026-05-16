const manifest = {"name":"LG Wheel Switch"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const call = api.call;
const callable = api.callable;
const addEventListener = api.addEventListener;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

const ACTIVE_DRIVER_CHANGED_EVENT = "activeDriverChanged";
const DRV_LSOG = "lgogwheelgamepad";
const DRV_LG4FF = "lg4ff";
const toggleDrivers = callable("toggle_drivers");
function LGWheelSwitchPlugin() {
    const [activeDriver, setActiveDriver] = SP_REACT.useState(null);
    const [loading, setLoading] = SP_REACT.useState(true);
    const [error, setError] = SP_REACT.useState(null);
    const detectAndSetDriver = SP_REACT.useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const detected = await call("detect_current_driver");
            if (detected !== undefined && detected !== null) {
                setActiveDriver(detected);
            }
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            setError(msg);
        }
        finally {
            setLoading(false);
        }
    }, []);
    SP_REACT.useEffect(() => {
        detectAndSetDriver();
        const handler = (data) => {
            setActiveDriver(data);
        };
        addEventListener(ACTIVE_DRIVER_CHANGED_EVENT, handler);
    }, [detectAndSetDriver]);
    const targetDriver = activeDriver === DRV_LSOG ? DRV_LG4FF : DRV_LSOG;
    const isLoading = loading || activeDriver === null;
    const buttonLabel = isLoading
        ? "Detecting driver..."
        : `Switch to ${targetDriver}`;
    const handleToggle = SP_REACT.useCallback(async () => {
        if (isLoading)
            return;
        setError(null);
        try {
            await toggleDrivers(targetDriver);
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            console.error("toggle_drivers failed:", msg);
            setError(msg);
        }
    }, [isLoading, targetDriver]);
    const handleSwitchToDriver = SP_REACT.useCallback(async (drv) => {
        setError(null);
        try {
            await toggleDrivers(drv);
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            console.error("toggle_drivers failed:", msg);
            setError(msg);
        }
    }, []);
    const switchToLG4FF = SP_REACT.useCallback(() => {
        handleSwitchToDriver(DRV_LG4FF);
    }, [handleSwitchToDriver]);
    const switchToLGOGWheelGamepad = SP_REACT.useCallback(() => {
        handleSwitchToDriver(DRV_LSOG);
    }, [handleSwitchToDriver]);
    return {
        name: "LG Wheel Switch",
        icon: (SP_JSX.jsx("svg", { width: "16", height: "16", viewBox: "0 0 16 16", fill: "currentColor", style: { marginRight: "8px" }, children: SP_JSX.jsx("path", { d: "M8 4.7a3.3 3.3 0 1 1 0 6.6 3.3 3.3 0 0 1 0-6.6zm0 1a2.3 2.3 0 1 0 0 4.6 2.3 2.3 0 0 0 0-4.6zM8 0a.8.8 0 0 1 .8.8v1.4a.8.8 0 0 1-1.6 0V.8A.8.8 0 0 1 8 0zm0 14.8a.8.8 0 0 1 .8.8v1.4a.8.8 0 0 1-1.6 0v-1.4a.8.8 0 0 1 .8-.8zM15.2 8a.8.8 0 0 1-.8.8h-1.4a.8.8 0 0 1 0-1.6h1.4a.8.8 0 0 1 .8.8zM2.2 8a.8.8 0 0 1-.8.8H0a.8.8 0 0 1 0-1.6h1.4a.8.8 0 0 1 .8.8zm13.07-5.29a.8.8 0 0 1 0 1.13l-1 1a.8.8 0 0 1-1.13-1.13l1-1a.8.8 0 0 1 1.13 0zM3.83 11.47a.8.8 0 0 1 0 1.13l-1 1a.8.8 0 0 1-1.13-1.13l1-1a.8.8 0 0 1 1.13 0zm10.14 3.54a.8.8 0 0 1-1.13 0l-1-1a.8.8 0 1 1 1.13-1.13l1 1a.8.8 0 0 1 0 1.13zM2.93 1.93a.8.8 0 0 1-1.13 0l-1-1a.8.8 0 0 1 1.13-1.13l1 1a.8.8 0 0 1 0 1.13z" }) })),
        content: (SP_JSX.jsxs(DFL.PanelSection, { title: "LG Wheel Switch", children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { children: ["Current driver: ", activeDriver ?? "—"] }) }), isLoading && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Spinner, {}) })), error && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { color: "red", textAlign: "center", width: "100%" }, children: ["Error: ", error] }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Button, { onClick: handleToggle, disabled: isLoading, children: buttonLabel }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Button, { onClick: switchToLG4FF, disabled: activeDriver === DRV_LG4FF, children: "Switch to lg4ff" }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Button, { onClick: switchToLGOGWheelGamepad, disabled: activeDriver === DRV_LSOG, children: "Switch to lgogwheelgamepad" }) })] })),
    };
}
var index = definePlugin(LGWheelSwitchPlugin);

export { index as default };
//# sourceMappingURL=index.js.map
