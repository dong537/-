from __future__ import annotations

from app.domain.providers import get_map_provider
from app.domain.store import get_trip_events, new_id, now_iso, record_event, store

WEST_LAKE_CENTER = {"lng": 120.148, "lat": 30.245}


def create_trip(payload: dict) -> dict:
    trip_id = new_id("trip")
    trip = {
        "id": trip_id,
        "destination": payload["destination"],
        "duration_minutes": payload["duration_minutes"],
        "preferences": payload.get("preferences", []),
        "use_panorama_camera": payload.get("use_panorama_camera", True),
        "current_location": payload.get("current_location"),
        "status": "created",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    store.trips[trip_id] = trip
    record_event(
        trip_id,
        "trip_created",
        "旅行目标已建立",
        f"目的地：{trip['destination']}，可用时间：{trip['duration_minutes']} 分钟。",
        {"preferences": trip["preferences"], "use_panorama_camera": trip["use_panorama_camera"]},
    )
    return trip


def _node(name: str, node_type: str, lng: float, lat: float, order: int, stay: int, walk: int, photo: int, rest: int, reason: str) -> dict:
    return {
        "id": new_id("node"),
        "name": name,
        "type": node_type,
        "lng": lng,
        "lat": lat,
        "order_index": order,
        "stay_minutes": stay,
        "walking_minutes": walk,
        "photo_value": photo,
        "rest_value": rest,
        "ai_reason": reason,
    }


def generate_initial_route(trip_id: str) -> dict:
    trip = store.trips[trip_id]
    route_id = new_id("route")
    map_context = get_map_provider().enrich_route_context(trip["destination"], trip["preferences"])
    relaxed = "轻松" in trip["preferences"] or "不要太累" in trip["destination"]
    nodes = [
        _node("西湖天地入口", "start", 120.1553, 30.2452, 1, 5, 0, 6, 5, "适合作为集合和开场点，离湖边路线很近。"),
        _node("湖边步道", "scenery", 120.1514, 30.2444, 2, 20, 8, 9, 4, "水面、树影和行人节奏都适合全景视频开头。"),
        _node("柳浪闻莺侧路", "photo_spot", 120.1484, 30.2396, 3, 25, 12, 9, 5, "路径相对安静，画面层次比主路更丰富。"),
        _node("湖畔咖啡休息点", "rest", 120.1502, 30.2425, 4, 25 if relaxed else 15, 7, 6, 9, "中途补充体力，也可以整理刚拍到的素材。"),
        _node("开阔湖景收尾点", "finish", 120.1456, 30.2461, 5, 15, 10, 8, 6, "适合作为路线结尾，能拍到更开阔的湖面。"),
    ]
    total = sum(item["stay_minutes"] + item["walking_minutes"] for item in nodes)
    route = {
        "route_id": route_id,
        "trip_id": trip_id,
        "route_name": "西湖轻松 City Walk",
        "summary": "以湖边风景、轻松步行和短视频拍摄为主，保留一个明确休息点。",
        "change_summary": None,
        "total_minutes": min(total, trip["duration_minutes"]),
        "nodes": nodes,
        "tips": [
            "前半段多拍环境，后半段保留体力。",
            "湖面反光强时，相机略微抬高会更稳。",
            "每到一个节点可以标记一次精彩瞬间。",
        ],
        "provider_context": map_context,
        "created_at": now_iso(),
    }
    trip["status"] = "route_ready"
    trip["updated_at"] = now_iso()
    store.routes[trip_id] = route
    record_event(
        trip_id,
        "route_generated",
        "AI 生成初始路线",
        f"生成 {len(nodes)} 个路线节点，总时长约 {route['total_minutes']} 分钟。",
        {"route_id": route_id, "node_names": [node["name"] for node in nodes]},
    )
    return route


def reroute(trip_id: str, status_action: str, remaining_minutes: int) -> dict:
    if trip_id not in store.routes:
        generate_initial_route(trip_id)
    current = store.routes[trip_id]
    route_id = new_id("route")

    action_copy = {
        "tired": "已缩短后半段路线，增加休息停留，并保留最值得拍的湖边节点。",
        "photo": "已把路线调整为更适合拍摄的节奏，增加开阔视角和安静侧路。",
        "food": "已优先加入附近用餐和咖啡休息点，减少连续步行。",
        "short_time": "已压缩路线，只保留最有代表性的两个拍摄节点和一个收尾点。",
        "quiet": "已避开主路，把路线改到更安静的侧路和湖畔小径。",
    }
    change_summary = action_copy.get(status_action, "已根据当前状态微调路线节奏。")

    nodes = [dict(node) for node in current["nodes"]]
    for index, node in enumerate(nodes):
        node["id"] = new_id("node")
        node["order_index"] = index + 1

    if status_action == "tired":
        nodes = nodes[:4]
        nodes[-1]["stay_minutes"] = max(nodes[-1]["stay_minutes"], 30)
        nodes[-1]["rest_value"] = 10
        nodes[-1]["ai_reason"] = "你现在体力下降，这里适合坐下来休息，也能拍到湖边氛围。"
    elif status_action == "photo":
        nodes.insert(2, _node("树影取景点", "photo_spot", 120.1491, 30.2435, 3, 18, 5, 10, 4, "树影、湖面和行人形成天然前中后景，适合短视频过渡。"))
    elif status_action == "food":
        nodes.insert(3, _node("南山路轻食点", "food", 120.1531, 30.2412, 4, 35, 6, 5, 9, "适合补充体力，离主路线不远。"))
    elif status_action == "short_time":
        nodes = [nodes[0], nodes[1], nodes[-1]]
        for node in nodes:
            node["stay_minutes"] = min(node["stay_minutes"], 12)
    elif status_action == "quiet":
        nodes[2]["name"] = "安静湖畔侧路"
        nodes[2]["ai_reason"] = "这段路人流更少，更适合慢慢走和录一段环境声。"
        nodes[2]["rest_value"] = 7

    for index, node in enumerate(nodes):
        node["order_index"] = index + 1
    total = min(sum(item["stay_minutes"] + item["walking_minutes"] for item in nodes), remaining_minutes)
    route = {
        "route_id": route_id,
        "trip_id": trip_id,
        "route_name": current["route_name"],
        "summary": current["summary"],
        "change_summary": change_summary,
        "total_minutes": total,
        "nodes": nodes,
        "tips": [
            change_summary,
            "路线已经尽量减少无效绕路。",
            "保留拍摄价值最高的节点，避免为了赶路牺牲出片质量。",
        ],
        "provider_context": current.get("provider_context"),
        "created_at": now_iso(),
    }
    store.trips[trip_id]["status"] = "rerouted"
    store.trips[trip_id]["updated_at"] = now_iso()
    store.routes[trip_id] = route
    record_event(
        trip_id,
        "route_updated",
        "根据用户状态调整路线",
        change_summary,
        {"status_action": status_action, "remaining_minutes": remaining_minutes, "route_id": route_id},
    )
    return route


def get_trip_detail(trip_id: str) -> dict:
    trip = store.trips[trip_id]
    route = store.routes.get(trip_id)
    media = [item for item in store.media.values() if item["trip_id"] == trip_id]
    frames = [item for item in store.frames.values() if item["trip_id"] == trip_id]
    exports = [item for item in store.exports.values() if item["trip_id"] == trip_id]
    return {"trip": trip, "route": route, "media": media, "frames": frames, "exports": exports, "events": get_trip_events(trip_id)}


def list_trip_summaries(limit: int = 10) -> list[dict]:
    trips = sorted(store.trips.values(), key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    summaries = []
    for trip in trips[:limit]:
        trip_id = trip["id"]
        summaries.append(
            {
                "trip_id": trip_id,
                "destination": trip["destination"],
                "duration_minutes": trip["duration_minutes"],
                "status": trip["status"],
                "created_at": trip["created_at"],
                "updated_at": trip["updated_at"],
                "route_ready": trip_id in store.routes,
                "media_count": len([item for item in store.media.values() if item["trip_id"] == trip_id]),
                "frame_count": len([item for item in store.frames.values() if item["trip_id"] == trip_id]),
                "export_count": len([item for item in store.exports.values() if item["trip_id"] == trip_id]),
                "event_count": len([item for item in store.events.values() if item["trip_id"] == trip_id]),
            }
        )
    return summaries
