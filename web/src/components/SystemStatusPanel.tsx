import { Activity, AlertTriangle, CheckCircle2, Database, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth, getReady, getRuntimeConfig, type HealthStatus, type ReadyStatus, type RuntimeConfig } from "../api/client";

type SystemSnapshot = {
  health?: HealthStatus;
  ready?: ReadyStatus;
  config?: RuntimeConfig & {
    counts?: Record<string, number>;
  };
  error?: string;
  updatedAt?: string;
};

function formatBytes(bytes?: number) {
  if (!bytes) return "-";
  if (bytes >= 1024 * 1024) return `${Math.round(bytes / 1024 / 1024)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

function formatTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function SystemStatusPanel() {
  const [snapshot, setSnapshot] = useState<SystemSnapshot>({});
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const [health, ready, config] = await Promise.all([getHealth(), getReady(), getRuntimeConfig()]);
      setSnapshot({ health, ready, config, updatedAt: new Date().toISOString() });
    } catch (error) {
      setSnapshot({
        error: error instanceof Error ? error.message : "Runtime status unavailable",
        updatedAt: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const ready = snapshot.ready?.status === "ready";
  const degraded = snapshot.ready?.status === "degraded" || snapshot.error;
  const checks = Object.entries(snapshot.ready?.checks ?? {});
  const counts = snapshot.config?.counts ?? {};

  return (
    <section className="system-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Runtime</p>
          <h2>系统状态</h2>
        </div>
        <button className="icon-only-button" disabled={loading} onClick={refresh} title="刷新系统状态" type="button">
          <RefreshCw className={loading ? "spin" : undefined} size={17} />
        </button>
      </div>

      <div className={ready ? "system-banner is-ready" : degraded ? "system-banner is-degraded" : "system-banner"}>
        {ready ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
        <div>
          <strong>{snapshot.error ? "API offline" : snapshot.ready?.status ?? "checking"}</strong>
          <span>{snapshot.health?.app_env ?? "unknown"} · {formatTime(snapshot.updatedAt)}</span>
        </div>
      </div>

      <div className="system-grid">
        <span>AI</span>
        <strong>{snapshot.health?.ai_provider ?? "-"} / {snapshot.health?.ai_mode ?? "-"}</strong>
        <span>Map</span>
        <strong>{snapshot.health?.map_provider ?? "-"} / {snapshot.health?.map_mode ?? "-"}</strong>
        <span>Upload</span>
        <strong>{formatBytes(snapshot.config?.max_upload_bytes)}</strong>
        <span>State</span>
        <strong>{snapshot.config?.store_persistence_enabled ? "snapshot on" : "memory only"}</strong>
      </div>

      {snapshot.config?.store_persistence_enabled && (
        <div className="state-row">
          <Database size={16} />
          <span>saved {formatTime(snapshot.config.store_saved_at)}</span>
        </div>
      )}

      {checks.length > 0 && (
        <div className="check-list">
          {checks.map(([name, ok]) => (
            <span className={ok ? "check-item is-ok" : "check-item is-bad"} key={name}>
              <Activity size={13} />
              {name}
            </span>
          ))}
        </div>
      )}

      {Object.keys(counts).length > 0 && (
        <div className="count-row">
          {Object.entries(counts).map(([name, value]) => (
            <span key={name}>
              <strong>{value}</strong>
              {name}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
