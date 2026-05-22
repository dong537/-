const AMAP_SCRIPT_ID = "amap-js-api";

declare global {
  interface Window {
    AMap?: any;
  }
}

export function getAmapKey() {
  return import.meta.env.VITE_AMAP_WEB_KEY || "";
}

export function loadAmap(key: string): Promise<any> {
  if (!key) {
    return Promise.reject(new Error("AMap key is not configured"));
  }

  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }

  const existing = document.getElementById(AMAP_SCRIPT_ID) as HTMLScriptElement | null;
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(window.AMap));
      existing.addEventListener("error", () => reject(new Error("Failed to load AMap")));
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = AMAP_SCRIPT_ID;
    script.async = true;
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`;
    script.onload = () => resolve(window.AMap);
    script.onerror = () => reject(new Error("Failed to load AMap"));
    document.head.appendChild(script);
  });
}
