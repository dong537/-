import type { RoutePlan } from "../types";

export function RouteTimeline({ route }: { route?: RoutePlan }) {
  if (!route) {
    return <div className="soft-panel">路线生成后会出现节点、停留时间和 AI 理由。</div>;
  }

  return (
    <div className="timeline">
      {route.nodes.map((node) => (
        <article className="timeline-item" key={node.id}>
          <div className="timeline-index">{node.order_index}</div>
          <div>
            <div className="timeline-title">
              <strong>{node.name}</strong>
              <span>{node.stay_minutes} 分钟停留</span>
            </div>
            <p>{node.ai_reason}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
