from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any

from app.domain.store import new_id, now_iso, persist_store, store

DEFAULT_USER_ID = "demo_user"

SCENE_LIBRARY = {
    "breakfast": {
        "category": "diet",
        "label": "balanced breakfast",
        "confidence": 0.91,
        "body_delta": 7,
        "mental_delta": 4,
        "impact": "规律早餐提升上午精力，对血糖稳定更友好。",
        "risk_flags": [],
        "recommendations": ["继续保持早餐蛋白质摄入", "搭配低糖水果和足量饮水"],
    },
    "late snack": {
        "category": "diet",
        "label": "late-night high-sugar snack",
        "confidence": 0.88,
        "body_delta": -18,
        "mental_delta": -8,
        "impact": "夜间加餐会增加血糖和体重管理压力，也可能影响睡眠质量。",
        "risk_flags": ["late_snack", "high_sugar"],
        "recommendations": ["睡前3小时避免高糖食物", "如饥饿可改为无糖酸奶或少量坚果"],
    },
    "workout": {
        "category": "exercise",
        "label": "moderate workout",
        "confidence": 0.93,
        "body_delta": 12,
        "mental_delta": 10,
        "impact": "中等强度运动有助于代谢、心肺功能和情绪恢复。",
        "risk_flags": [],
        "recommendations": ["保持每周3-5次中等强度运动", "运动后补水并进行5分钟拉伸"],
    },
    "sitting": {
        "category": "daily",
        "label": "long sitting desk work",
        "confidence": 0.9,
        "body_delta": -12,
        "mental_delta": -6,
        "impact": "长时间久坐会增加肩颈、腰背和代谢负担，也容易累积压力。",
        "risk_flags": ["sedentary"],
        "recommendations": ["每45分钟起身活动3分钟", "午后安排一次10分钟步行"],
    },
    "sleep": {
        "category": "sleep",
        "label": "regular sleep",
        "confidence": 0.89,
        "body_delta": 9,
        "mental_delta": 12,
        "impact": "规律睡眠有助于内分泌稳定、情绪恢复和白天专注。",
        "risk_flags": [],
        "recommendations": ["固定入睡时间", "睡前30分钟减少屏幕刺激"],
    },
    "outdoor walk": {
        "category": "daily",
        "label": "outdoor relaxation",
        "confidence": 0.87,
        "body_delta": 6,
        "mental_delta": 13,
        "impact": "户外放松能缓解压力，并提高日间活动量。",
        "risk_flags": [],
        "recommendations": ["工作日保留15分钟户外步行", "优先选择光照充足的时段"],
    },
}

DEMO_SCENES = ["breakfast", "sitting", "workout", "late snack", "sleep", "outdoor walk"]


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _date_key(value: str | None = None) -> str:
    return _parse_dt(value).date().isoformat()


def _week_bounds(date_key: str | None = None) -> tuple[str, str]:
    current = datetime.fromisoformat(date_key or datetime.now(UTC).date().isoformat()).date()
    start = current - timedelta(days=current.weekday())
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def _calculate_bmi(vital_signs: dict[str, Any]) -> float:
    if vital_signs.get("bmi"):
        return round(float(vital_signs["bmi"]), 1)
    height_m = float(vital_signs["height_cm"]) / 100
    return round(float(vital_signs["weight_kg"]) / (height_m * height_m), 1)


def _vital_warnings(vital_signs: dict[str, Any]) -> list[str]:
    bmi = _calculate_bmi(vital_signs)
    warnings: list[str] = []
    if bmi < 18.5:
        warnings.append("BMI偏低，需关注营养摄入。")
    elif bmi >= 28:
        warnings.append("BMI达到肥胖区间，建议控制总热量并增加运动。")
    elif bmi >= 24:
        warnings.append("BMI偏高，建议关注体重管理。")
    if vital_signs["systolic_bp"] >= 140 or vital_signs["diastolic_bp"] >= 90:
        warnings.append("血压偏高，本周报告会提高高盐、高脂饮食风险权重。")
    if vital_signs["heart_rate"] > 100:
        warnings.append("静息心率偏高，建议关注压力、睡眠和咖啡因摄入。")
    if vital_signs["blood_oxygen"] < 95:
        warnings.append("血氧偏低，若持续异常建议及时就医。")
    if vital_signs.get("blood_glucose") and vital_signs["blood_glucose"] >= 7:
        warnings.append("血糖偏高，高糖饮食将被标记为重点风险。")
    if vital_signs.get("uric_acid") and vital_signs["uric_acid"] >= 420:
        warnings.append("尿酸偏高，建议控制高嘌呤饮食。")
    return warnings


def _latest_metric(user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None:
    metrics = [metric for metric in store.health_metrics.values() if metric["user_id"] == user_id]
    if not metrics:
        return None
    return sorted(metrics, key=lambda metric: metric["recorded_at"], reverse=True)[0]


def _profile_for_user(user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None:
    profiles = [profile for profile in store.health_profiles.values() if profile["user_id"] == user_id]
    if not profiles:
        return None
    profile = sorted(profiles, key=lambda item: item["updated_at"], reverse=True)[0]
    return _profile_response(profile, include_history=False)


def _profile_response(profile: dict[str, Any], include_history: bool = True) -> dict[str, Any]:
    metrics = [metric for metric in store.health_metrics.values() if metric["profile_id"] == profile["profile_id"]]
    metrics = sorted(metrics, key=lambda item: item["recorded_at"], reverse=True)
    return {
        **profile,
        "latest_metric": metrics[0] if metrics else None,
        "metric_history": metrics[:30] if include_history else [],
    }


def _device_for_user(user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None:
    devices = [device for device in store.devices.values() if device["user_id"] == user_id]
    if not devices:
        return None
    return sorted(devices, key=lambda item: item["updated_at"], reverse=True)[0]


def upsert_health_profile(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = payload.get("user_id") or DEFAULT_USER_ID
    existing = next((profile for profile in store.health_profiles.values() if profile["user_id"] == user_id), None)
    timestamp = now_iso()
    if existing:
        existing.update(
            {
                "name": payload["name"],
                "age": payload["age"],
                "gender": payload["gender"],
                "updated_at": timestamp,
            }
        )
        profile = existing
    else:
        profile = {
            "profile_id": new_id("profile"),
            "user_id": user_id,
            "name": payload["name"],
            "age": payload["age"],
            "gender": payload["gender"],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        store.health_profiles[profile["profile_id"]] = profile

    vital_signs = dict(payload["vital_signs"])
    vital_signs["bmi"] = _calculate_bmi(vital_signs)
    metric = {
        "metric_id": new_id("metric"),
        "profile_id": profile["profile_id"],
        "user_id": user_id,
        "recorded_at": timestamp,
        "vital_signs": vital_signs,
        "warnings": _vital_warnings(vital_signs),
    }
    store.health_metrics[metric["metric_id"]] = metric
    persist_store()
    return _profile_response(profile)


def bind_device(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = payload.get("user_id") or DEFAULT_USER_ID
    timestamp = now_iso()
    device = {
        "device_id": new_id("device"),
        "user_id": user_id,
        "device_name": payload["device_name"],
        "device_model": payload["device_model"],
        "provider": "insta360_mock_sdk",
        "connection_type": payload["connection_type"],
        "status": "online",
        "battery_percent": 86,
        "storage_free_gb": 58.4,
        "auto_capture_enabled": payload["auto_capture_enabled"],
        "capture_interval_minutes": payload["capture_interval_minutes"],
        "capture_window": payload["capture_window"],
        "last_seen_at": timestamp,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    store.devices[device["device_id"]] = device
    persist_store()
    return device


def update_device(device_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    device = store.devices.get(device_id)
    if not device:
        return None
    for key, value in payload.items():
        if value is not None:
            device[key] = value
    device["updated_at"] = now_iso()
    device["last_seen_at"] = device["updated_at"]
    persist_store()
    return device


def _scene_from_hint(scene_hint: str | None) -> dict[str, Any]:
    hint = (scene_hint or "").strip().lower()
    if not hint:
        hint = DEMO_SCENES[len(store.captures) % len(DEMO_SCENES)]
    for key, scene in SCENE_LIBRARY.items():
        if key in hint or scene["category"] in hint or scene["label"] in hint:
            return scene
    return SCENE_LIBRARY["sitting"]


def _score_behavior(scene: dict[str, Any], user_id: str) -> tuple[int, int, list[str], list[str]]:
    body_score = 78 + int(scene["body_delta"])
    mental_score = 76 + int(scene["mental_delta"])
    risk_flags = list(scene["risk_flags"])
    recommendations = list(scene["recommendations"])
    metric = _latest_metric(user_id)
    vitals = metric["vital_signs"] if metric else {}
    if vitals.get("blood_glucose", 0) >= 7 and "high_sugar" in risk_flags:
        body_score -= 10
        recommendations.append("血糖偏高时建议记录餐后2小时血糖变化。")
    if (vitals.get("systolic_bp", 0) >= 140 or vitals.get("diastolic_bp", 0) >= 90) and scene["category"] == "diet":
        recommendations.append("血压偏高时优先选择少盐、少油饮食。")
    if vitals.get("bmi", 0) >= 24 and scene["category"] == "exercise":
        body_score += 4
        recommendations.append("当前BMI偏高，运动行为对体重管理收益更高。")
    return max(0, min(body_score, 100)), max(0, min(mental_score, 100)), risk_flags, recommendations


def _behavior_for_capture(capture: dict[str, Any]) -> dict[str, Any]:
    scene = _scene_from_hint(capture.get("scene_hint"))
    body_score, mental_score, risk_flags, recommendations = _score_behavior(scene, capture["user_id"])
    behavior = {
        "behavior_id": new_id("behavior"),
        "capture_id": capture["capture_id"],
        "user_id": capture["user_id"],
        "category": scene["category"],
        "label": scene["label"],
        "confidence": scene["confidence"],
        "body_score": body_score,
        "mental_score": mental_score,
        "impact": scene["impact"],
        "risk_flags": risk_flags,
        "recommendations": recommendations,
        "created_at": now_iso(),
    }
    store.behavior_records[behavior["behavior_id"]] = behavior
    return behavior


def create_capture(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = payload.get("user_id") or DEFAULT_USER_ID
    device_id = payload.get("device_id")
    if not device_id:
        device = _device_for_user(user_id)
        device_id = device["device_id"] if device else None
    captured_at = _parse_dt(payload.get("captured_at")).isoformat()
    capture = {
        "capture_id": new_id("capture"),
        "user_id": user_id,
        "device_id": device_id,
        "capture_mode": payload["capture_mode"],
        "scene_hint": payload.get("scene_hint"),
        "image_url": payload.get("image_url") or f"/files/health-demo/{new_id('scene')}.jpg",
        "status": "analyzed",
        "special_tag": "manual_priority" if payload["capture_mode"] == "manual" else None,
        "captured_at": captured_at,
        "synced_at": now_iso(),
    }
    behavior = _behavior_for_capture(capture)
    capture["analysis"] = behavior
    store.captures[capture["capture_id"]] = capture

    if device_id and device_id in store.devices:
        device = store.devices[device_id]
        device["last_seen_at"] = capture["synced_at"]
        device["status"] = "online"
        device["updated_at"] = capture["synced_at"]
    persist_store()
    return capture


def _captures_for_day(user_id: str, date_key: str) -> list[dict[str, Any]]:
    return [
        capture
        for capture in store.captures.values()
        if capture["user_id"] == user_id and _date_key(capture["captured_at"]) == date_key
    ]


def _behavior_summary(behaviors: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(behavior["category"] for behavior in behaviors)
    labels = Counter(behavior["label"] for behavior in behaviors)
    return {
        "diet_count": counts.get("diet", 0),
        "exercise_count": counts.get("exercise", 0),
        "sleep_count": counts.get("sleep", 0),
        "daily_count": counts.get("daily", 0),
        "top_behaviors": labels.most_common(5),
        "total_records": len(behaviors),
    }


def generate_daily_log(user_id: str = DEFAULT_USER_ID, date_key: str | None = None) -> dict[str, Any]:
    date_value = date_key or datetime.now(UTC).date().isoformat()
    captures = _captures_for_day(user_id, date_value)
    behaviors = [capture["analysis"] for capture in captures if capture.get("analysis")]
    body_score = round(mean([behavior["body_score"] for behavior in behaviors])) if behaviors else 76
    mental_score = round(mean([behavior["mental_score"] for behavior in behaviors])) if behaviors else 76
    overall_score = round(body_score * 0.56 + mental_score * 0.44)
    risk_flags = sorted({flag for behavior in behaviors for flag in behavior["risk_flags"]})
    abnormal_map = {
        "late_snack": "夜间加餐",
        "high_sugar": "高糖饮食",
        "sedentary": "长时间久坐",
    }
    abnormal_behaviors = [abnormal_map.get(flag, flag) for flag in risk_flags]
    risk_tips = sorted({tip for behavior in behaviors for tip in behavior["recommendations"]})[:6]
    daily_log = {
        "daily_log_id": f"daily_{user_id}_{date_value}",
        "user_id": user_id,
        "date": date_value,
        "overall_score": overall_score,
        "body_score": body_score,
        "mental_score": mental_score,
        "behavior_summary": _behavior_summary(behaviors),
        "abnormal_behaviors": abnormal_behaviors,
        "risk_tips": risk_tips or ["今日行为数据较少，建议保持自动采集以提升分析准确性。"],
        "generated_at": now_iso(),
    }
    store.daily_logs[daily_log["daily_log_id"]] = daily_log
    persist_store()
    return daily_log


def _daily_logs_for_week(user_id: str, week_start: str, week_end: str) -> list[dict[str, Any]]:
    start = datetime.fromisoformat(week_start).date()
    end = datetime.fromisoformat(week_end).date()
    return [
        log
        for log in store.daily_logs.values()
        if log["user_id"] == user_id and start <= datetime.fromisoformat(log["date"]).date() <= end
    ]


def generate_weekly_report(user_id: str = DEFAULT_USER_ID, date_key: str | None = None) -> dict[str, Any]:
    week_start, week_end = _week_bounds(date_key)
    logs = _daily_logs_for_week(user_id, week_start, week_end)
    if not logs:
        logs = [generate_daily_log(user_id, date_key or datetime.now(UTC).date().isoformat())]

    all_captures = []
    start = datetime.fromisoformat(week_start).date()
    end = datetime.fromisoformat(week_end).date()
    for capture in store.captures.values():
        capture_date = _parse_dt(capture["captured_at"]).date()
        if capture["user_id"] == user_id and start <= capture_date <= end:
            all_captures.append(capture)
    behaviors = [capture["analysis"] for capture in all_captures if capture.get("analysis")]
    category_counts = Counter(behavior["category"] for behavior in behaviors)
    risk_flags = Counter(flag for behavior in behaviors for flag in behavior["risk_flags"])
    avg_body = round(mean([log["body_score"] for log in logs]))
    avg_mental = round(mean([log["mental_score"] for log in logs]))
    avg_overall = round(mean([log["overall_score"] for log in logs]))
    suggestions = {
        "diet": ["晚餐后避免高糖加餐，连续7天记录睡前饥饿感。", "每日至少一餐保证优质蛋白和蔬菜。"],
        "exercise": ["每周完成3次20分钟中等强度运动。", "久坐日设置45分钟起身提醒。"],
        "sleep": ["将入睡时间提前到23:30前，睡前30分钟减少屏幕刺激。"],
        "mind": ["每天安排10-15分钟户外步行或呼吸放松。"],
    }
    if risk_flags.get("high_sugar"):
        suggestions["diet"].insert(0, "本周高糖风险偏高，建议减少含糖饮料和夜间甜食。")
    if risk_flags.get("sedentary"):
        suggestions["exercise"].insert(0, "本周久坐较多，优先把碎片化步行纳入日程。")

    report = {
        "report_id": f"weekly_{user_id}_{week_start}",
        "user_id": user_id,
        "week_start": week_start,
        "week_end": week_end,
        "average_overall_score": avg_overall,
        "average_body_score": avg_body,
        "average_mental_score": avg_mental,
        "trend": [
            {
                "date": log["date"],
                "overall_score": log["overall_score"],
                "body_score": log["body_score"],
                "mental_score": log["mental_score"],
            }
            for log in sorted(logs, key=lambda item: item["date"])
        ],
        "behavior_analysis": {
            "diet": category_counts.get("diet", 0),
            "exercise": category_counts.get("exercise", 0),
            "sleep": category_counts.get("sleep", 0),
            "daily": category_counts.get("daily", 0),
            "risk_flags": dict(risk_flags),
        },
        "body_assessment": f"本周身体维度平均{avg_body}分，主要受饮食规律、运动频次和久坐行为影响。",
        "mental_assessment": f"本周心理维度平均{avg_mental}分，户外放松和睡眠规律对精力恢复贡献较高。",
        "suggestions": suggestions,
        "next_week_goals": [
            "连续5天完成核心体征更新或确认。",
            "至少3天在午后进行10分钟步行。",
            "减少夜间高糖加餐至每周不超过1次。",
        ],
        "comparison": "暂无上周完整数据，已建立本周基线。",
        "generated_at": now_iso(),
    }
    store.weekly_reports[report["report_id"]] = report
    persist_store()
    return report


def get_dashboard(user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    profile = _profile_for_user(user_id)
    device = _device_for_user(user_id)
    today_key = datetime.now(UTC).date().isoformat()
    today_log = store.daily_logs.get(f"daily_{user_id}_{today_key}")
    week_start, _ = _week_bounds(today_key)
    weekly_report = store.weekly_reports.get(f"weekly_{user_id}_{week_start}")
    captures = sorted(
        [capture for capture in store.captures.values() if capture["user_id"] == user_id],
        key=lambda item: item["captured_at"],
        reverse=True,
    )
    behaviors = sorted(
        [behavior for behavior in store.behavior_records.values() if behavior["user_id"] == user_id],
        key=lambda item: item["created_at"],
        reverse=True,
    )
    metrics = sorted(
        [metric for metric in store.health_metrics.values() if metric["user_id"] == user_id],
        key=lambda item: item["recorded_at"],
        reverse=True,
    )
    return {
        "profile": profile,
        "device": device,
        "today_log": today_log,
        "weekly_report": weekly_report,
        "recent_captures": captures[:8],
        "recent_behaviors": behaviors[:8],
        "metric_trend": metrics[:30],
        "status": {
            "profile_ready": profile is not None,
            "device_ready": device is not None,
            "capture_count": len(captures),
            "behavior_count": len(behaviors),
            "daily_log_ready": today_log is not None,
            "weekly_report_ready": weekly_report is not None,
        },
    }


def run_demo_flow(user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    profile = upsert_health_profile(
        {
            "user_id": user_id,
            "name": "Demo User",
            "age": 32,
            "gender": "unspecified",
            "vital_signs": {
                "height_cm": 172,
                "weight_kg": 76,
                "bmi": None,
                "systolic_bp": 132,
                "diastolic_bp": 86,
                "heart_rate": 82,
                "blood_oxygen": 98,
                "blood_glucose": 7.2,
                "blood_lipid": 5.4,
                "uric_acid": 398,
                "notes": "Demo baseline generated from PRD flow.",
            },
        }
    )
    device = _device_for_user(user_id) or bind_device(
        {
            "user_id": user_id,
            "device_name": "Insta360 X4",
            "device_model": "Insta360 X4",
            "connection_type": "mock",
            "auto_capture_enabled": True,
            "capture_interval_minutes": 10,
            "capture_window": "08:00-22:00",
        }
    )

    captures = []
    now = datetime.now(UTC)
    for index, scene in enumerate(DEMO_SCENES):
        captures.append(
            create_capture(
                {
                    "user_id": user_id,
                    "device_id": device["device_id"],
                    "capture_mode": "manual" if index in {2, 3} else "auto",
                    "scene_hint": scene,
                    "captured_at": (now - timedelta(minutes=(len(DEMO_SCENES) - index) * 12)).isoformat(),
                }
            )
        )
    today_log = generate_daily_log(user_id)
    weekly_report = generate_weekly_report(user_id)
    return {
        "profile": profile,
        "device": device,
        "captures": captures,
        "today_log": today_log,
        "weekly_report": weekly_report,
    }
