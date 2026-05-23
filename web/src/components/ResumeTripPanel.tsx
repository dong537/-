import { Clock3, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { getTripDetail, listTrips } from "../api/client";
import type { TripSummary } from "../types";

function formatRelative(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return date.toLocaleDateString();
}

export function ResumeTripPanel({
  activeTripId,
  busy,
  onResume
}: {
  activeTripId?: string;
  busy?: boolean;
  onResume: (tripId: string, detail: Awaited<ReturnType<typeof getTripDetail>>) => void;
}) {
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setTrips(await listTrips(5));
    } catch {
      setTrips([]);
    } finally {
      setLoading(false);
    }
  }

  async function resume(tripId: string) {
    setLoading(true);
    try {
      const detail = await getTripDetail(tripId);
      onResume(tripId, detail);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [activeTripId]);

  return (
    <section className="resume-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Resume</p>
          <h2>最近演示</h2>
        </div>
        <button className="icon-only-button" disabled={loading || busy} onClick={refresh} title="刷新最近演示" type="button">
          <RotateCcw className={loading ? "spin" : undefined} size={17} />
        </button>
      </div>

      {trips.length === 0 ? (
        <p className="small-muted">还没有可恢复的演示。</p>
      ) : (
        <div className="resume-list">
          {trips.map((trip) => (
            <button className={trip.trip_id === activeTripId ? "resume-item is-active" : "resume-item"} disabled={busy || loading} key={trip.trip_id} onClick={() => resume(trip.trip_id)} type="button">
              <div>
                <strong>{trip.destination}</strong>
                <span>{trip.status} · {trip.duration_minutes} min</span>
              </div>
              <div className="resume-meta">
                <Clock3 size={13} />
                <span>{formatRelative(trip.updated_at)}</span>
              </div>
              <div className="resume-counts">
                <span>{trip.frame_count} frames</span>
                <span>{trip.export_count} exports</span>
                <span>{trip.event_count} events</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
