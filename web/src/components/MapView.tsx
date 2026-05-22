import { Camera, Coffee, Flag, MapPin, Trees } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ComponentType } from "react";
import type { RouteNode, RoutePlan } from "../types";
import { getAmapKey, loadAmap } from "../utils/amapLoader";

const iconMap: Record<string, ComponentType<{ size?: number }>> = {
  start: MapPin,
  scenery: Trees,
  photo_spot: Camera,
  rest: Coffee,
  food: Coffee,
  finish: Flag
};

function nodeIcon(node: RouteNode) {
  const Icon = iconMap[node.type] ?? MapPin;
  return <Icon size={18} />;
}

export function MapView({ route }: { route?: RoutePlan }) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const [mapMode, setMapMode] = useState<"demo" | "amap" | "failed">(getAmapKey() ? "amap" : "demo");

  useEffect(() => {
    if (!route || !mapRef.current) return;
    const key = getAmapKey();
    if (!key) {
      setMapMode("demo");
      return;
    }

    let cancelled = false;
    loadAmap(key)
      .then((AMap) => {
        if (cancelled || !mapRef.current) return;
        setMapMode("amap");
        mapRef.current.innerHTML = "";
        const center = [route.nodes[0].lng, route.nodes[0].lat];
        const map = new AMap.Map(mapRef.current, {
          center,
          zoom: 15,
          mapStyle: "amap://styles/macaron"
        });
        mapInstanceRef.current = map;

        const path = route.nodes.map((node) => [node.lng, node.lat]);
        const polyline = new AMap.Polyline({
          path,
          strokeColor: "#2d604b",
          strokeWeight: 7,
          strokeOpacity: 0.85,
          lineJoin: "round"
        });
        map.add(polyline);

        route.nodes.forEach((node) => {
          const marker = new AMap.Marker({
            position: [node.lng, node.lat],
            title: node.name,
            label: {
              content: node.name,
              direction: "top"
            }
          });
          map.add(marker);
        });
        map.setFitView();
      })
      .catch(() => setMapMode("failed"));

    return () => {
      cancelled = true;
      mapInstanceRef.current?.destroy?.();
      mapInstanceRef.current = null;
    };
  }, [route]);

  if (!route) {
    return (
      <section className="map-panel empty-map">
        <MapPin size={28} />
        <p>生成路线后，这里会展示地图和路线节点。</p>
      </section>
    );
  }

  return (
    <section className="map-panel">
      {mapMode === "amap" ? (
        <div className="real-map-canvas" ref={mapRef} aria-label="高德路线地图" />
      ) : (
        <div className="map-canvas" aria-label="演示路线地图">
          <div className="lake-shape" />
          <div className="route-line" />
          {route.nodes.map((node, index) => (
            <div className={`map-marker marker-${index + 1}`} key={node.id} title={node.name}>
              {nodeIcon(node)}
            </div>
          ))}
          {mapMode === "failed" ? <div className="map-fallback-badge">地图 Key 加载失败，已切回演示图</div> : null}
        </div>
      )}
      <div className="route-summary">
        <div>
          <p className="eyebrow">当前路线</p>
          <h2>{route.route_name}</h2>
        </div>
        <span>{route.total_minutes} 分钟</span>
      </div>
      <p className="muted">{route.change_summary ?? route.summary}</p>
    </section>
  );
}
