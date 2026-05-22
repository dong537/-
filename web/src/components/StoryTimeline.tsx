import { Camera, FileDown, Flag, MapPinned, MessageCircle, Sparkles, Star } from "lucide-react";
import type { ComponentType } from "react";
import type { TripEvent } from "../types";

const eventIcons: Record<string, ComponentType<{ size?: number }>> = {
  trip_created: Flag,
  route_generated: MapPinned,
  route_updated: MapPinned,
  media_uploaded: Camera,
  demo_media_created: Camera,
  frames_extracted: Camera,
  frame_marked: Star,
  frame_unmarked: Star,
  companion_generated: MessageCircle,
  export_generated: FileDown
};

export function StoryTimeline({ events }: { events: TripEvent[] }) {
  if (!events.length) {
    return <div className="soft-panel">操作旅程后，这里会沉淀路线、素材、讲解和出片事件。</div>;
  }

  return (
    <section className="story-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">故事线</p>
          <h2>旅程事件</h2>
        </div>
        <Sparkles size={19} />
      </div>
      <div className="story-list">
        {events.map((event) => {
          const Icon = eventIcons[event.event_type] ?? Sparkles;
          const time = new Date(event.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          return (
            <article className="story-item" key={event.event_id}>
              <div className="story-icon">
                <Icon size={16} />
              </div>
              <div>
                <div className="story-title">
                  <strong>{event.title}</strong>
                  <span>{time}</span>
                </div>
                <p>{event.detail}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
