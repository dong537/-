from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.domain.store import now_iso

PROVIDER_ID = "insta360_android_sdk_v1_9_11_bridge"
SDK_VERSION = "1.9.11"
SUPPORTED_OPERATIONS = ("bind", "capture", "sync", "export", "status")


FEATURES: list[dict[str, Any]] = [
    {
        "key": "sdk_init",
        "name": "SDK 初始化",
        "sdk_calls": ["UsbMgr.init", "InstaCameraSDK.init", "InstaMediaSDK.init", "LogManager"],
        "demo_files": ["InstaApp.kt"],
        "project_usage": "Android 端启动时初始化相机、媒体和日志模块，后端只记录 provider 状态。",
    },
    {
        "key": "ble_scan",
        "name": "BLE 发现",
        "sdk_calls": ["InstaCameraManager.setScanBleListener", "startBleScan", "stopBleScan"],
        "demo_files": ["ui/connect/ConnectViewModel.kt", "ui/connect/ConnectFragment.kt"],
        "project_usage": "用于设备发现、最近设备唤醒和绑定前置流程。",
    },
    {
        "key": "device_connect",
        "name": "Wi-Fi/USB/BLE 连接",
        "sdk_calls": ["connectBle", "openCamera(CONNECT_TYPE_WIFI)", "openCamera(CONNECT_TYPE_USB)", "setNetIdToCamera"],
        "demo_files": ["ui/connect/ConnectViewModel.kt", "service/ConnectService.java", "usb/UsbMgr.kt"],
        "project_usage": "真实 Android 桥接层把连接状态、电量、存储空间同步给健康设备模型。",
    },
    {
        "key": "camera_status",
        "name": "相机状态",
        "sdk_calls": ["fetchCameraOptions", "mediaTime", "cameraStorageFreeSpace", "getRemaining"],
        "demo_files": ["ui/connect/ConnectViewModel.kt", "ui/capture/CaptureViewModel.kt"],
        "project_usage": "映射到设备状态、电量、剩余容量、离线缓存数量和最近在线时间。",
    },
    {
        "key": "preview_stream",
        "name": "预览流",
        "sdk_calls": ["startPreviewStream", "restartPreviewStream", "closePreviewStream", "setPreviewStatusChangedListener"],
        "demo_files": ["ui/capture/CaptureViewModel.kt"],
        "project_usage": "用于 App 端实时预览和采集前参数校验，后端不直接处理预览流。",
    },
    {
        "key": "capture_control",
        "name": "抓拍/录制",
        "sdk_calls": ["startNormalCapture", "startHDRCapture", "startNormalRecord", "startIntervalShooting", "stopIntervalShooting"],
        "demo_files": ["ui/capture/CaptureViewModel.kt", "ui/shot/ShotViewModel.kt"],
        "project_usage": "映射到手动抓拍、自动定时采集和离线缓存影像记录。",
    },
    {
        "key": "album_sync",
        "name": "相册同步",
        "sdk_calls": ["WorkUtils.getAllCameraWorks", "WorkUtils.getAllLocalWorks", "OkGo.get", "deleteFileList"],
        "demo_files": ["ui/album/AlbumViewModel.kt"],
        "project_usage": "把相机作品列表、下载进度和本地作品同步为健康采集输入。",
    },
    {
        "key": "media_export",
        "name": "媒体播放/导出",
        "sdk_calls": ["ExportUtils.exportImage", "ExportUtils.exportVideo", "StitchUtils.generateHDR", "StitchUtils.generatePureShot"],
        "demo_files": ["ui/play/WorkPlayViewModel.kt", "glide/WorkDataFetcher.kt"],
        "project_usage": "把全景图、视频、HDR/PureShot 输出交给健康分析或后续报告附件。",
    },
]


WORKFLOWS: dict[str, dict[str, Any]] = {
    "bind": {
        "title": "设备发现与绑定",
        "recommended_connection": "BLE 发现后切换 Wi-Fi 或 USB",
        "backend_handoff": "POST /api/health/devices/bind",
        "safety_checks": ["蓝牙和定位权限已授权", "设备型号在 supportCameraType 内", "Wi-Fi 网络绑定成功后再打开相机"],
        "steps": [
            {
                "order": 1,
                "name": "初始化 SDK",
                "sdk_calls": ["InstaCameraSDK.init(app)", "InstaMediaSDK.init(app)", "UsbMgr.init(context)"],
                "demo_files": ["InstaApp.kt"],
                "backend_event": "记录 provider=insta360_android_sdk_v1_9_11_bridge",
                "notes": "Android Application 启动时完成，相机能力不进入后端源码依赖。",
            },
            {
                "order": 2,
                "name": "扫描设备",
                "sdk_calls": ["setScanBleListener(listener)", "startBleScan()"],
                "demo_files": ["ui/connect/ConnectViewModel.kt"],
                "backend_event": "展示候选设备并等待用户确认绑定",
                "notes": "扫描结果保留设备名、型号、序列号后六位即可。",
            },
            {
                "order": 3,
                "name": "建立连接",
                "sdk_calls": ["connectBle(bleDevice)", "openCamera(CONNECT_TYPE_WIFI)", "openCamera(CONNECT_TYPE_USB)"],
                "demo_files": ["ui/connect/ConnectViewModel.kt", "service/ConnectService.java"],
                "backend_event": "创建设备记录，状态置为 online",
                "notes": "Wi-Fi 连接成功后需要 bindProcessToNetwork，再调用 setNetIdToCamera。",
            },
            {
                "order": 4,
                "name": "同步基础状态",
                "sdk_calls": ["fetchCameraOptions(callback)", "cameraStorageFreeSpace", "mediaTime"],
                "demo_files": ["ui/connect/ConnectViewModel.kt"],
                "backend_event": "写入 battery_percent、storage_free_gb、last_seen_at",
                "notes": "失败时更新 status_detail，保留离线缓存入口。",
            },
        ],
    },
    "capture": {
        "title": "自动/手动采集",
        "recommended_connection": "Wi-Fi 或 USB",
        "backend_handoff": "POST /api/health/captures",
        "safety_checks": ["SD 卡可用", "剩余容量足够", "采集窗口命中", "当前不是相机工作中冲突状态"],
        "steps": [
            {
                "order": 1,
                "name": "读取相机能力",
                "sdk_calls": ["fetchCameraOptions(callback)", "initCameraSupportConfig(callback)", "getSupportCaptureMode()"],
                "demo_files": ["ui/capture/CaptureViewModel.kt"],
                "backend_event": "校验设备在线和采集配置",
                "notes": "旧控制流需要把 offline capture setting 批量下发到相机。",
            },
            {
                "order": 2,
                "name": "打开预览流",
                "sdk_calls": ["startPreviewStream(PREVIEW_TYPE_NORMAL)", "setPreviewStatusChangedListener(listener)"],
                "demo_files": ["ui/capture/CaptureViewModel.kt"],
                "backend_event": "App 端展示预览，后端等待采集结果元数据",
                "notes": "预览编码或防抖参数变化时重启播放器。",
            },
            {
                "order": 3,
                "name": "执行采集",
                "sdk_calls": ["startNormalCapture()", "startHDRCapture()", "startIntervalShooting()", "startNormalRecord()"],
                "demo_files": ["ui/capture/CaptureViewModel.kt", "ui/shot/ShotViewModel.kt"],
                "backend_event": "创建 manual/auto/offline_cache capture",
                "notes": "自动采集使用 capture_interval_minutes 和 capture_window 控制触发。",
            },
            {
                "order": 4,
                "name": "回传状态",
                "sdk_calls": ["setCaptureStatusListener(listener)", "onCaptureFinish(paths)", "onCaptureError(code)"],
                "demo_files": ["ui/capture/CaptureViewModel.kt"],
                "backend_event": "成功时触发 AI 行为分析，失败时标记 needs_review 或缓存",
                "notes": "离线时只保存本地路径和场景线索，联网后再同步。",
            },
        ],
    },
    "sync": {
        "title": "离线缓存同步",
        "recommended_connection": "Wi-Fi 或 USB",
        "backend_handoff": "POST /api/health/devices/{device_id}/sync",
        "safety_checks": ["相机网络已绑定", "本地作品目录可写", "重复文件已去重"],
        "steps": [
            {
                "order": 1,
                "name": "拉取相机作品",
                "sdk_calls": ["WorkUtils.getAllCameraWorks()", "WorkUtils.getAllLocalWorks(workDir)"],
                "demo_files": ["ui/album/AlbumViewModel.kt"],
                "backend_event": "比较相机作品和本地健康采集记录",
                "notes": "BLE 连接只用于发现，不用于拉取完整作品。",
            },
            {
                "order": 2,
                "name": "下载素材",
                "sdk_calls": ["OkGo.get(url).execute(FileCallback)", "downloadProgress(progress)"],
                "demo_files": ["ui/album/AlbumViewModel.kt"],
                "backend_event": "把下载完成的 image_url 写入 capture",
                "notes": "下载期间需要绑定到 cameraNet，结束后解除绑定。",
            },
            {
                "order": 3,
                "name": "补做分析",
                "sdk_calls": ["onSuccess(response)", "onError(response)"],
                "demo_files": ["ui/album/AlbumViewModel.kt"],
                "backend_event": "sync_offline_captures 触发 AI 分析并清空缓存计数",
                "notes": "失败素材保留 cached 状态，下一轮继续同步。",
            },
        ],
    },
    "export": {
        "title": "全景媒体导出",
        "recommended_connection": "本地文件",
        "backend_handoff": "健康报告附件或后续媒体分析输入",
        "safety_checks": ["素材 extra data 已加载", "导出目录可写", "分辨率和码率在设备能力范围内"],
        "steps": [
            {
                "order": 1,
                "name": "构建播放参数",
                "sdk_calls": ["VideoParamsBuilder()", "ImageParamsBuilder()", "loadExtraData()"],
                "demo_files": ["ui/play/WorkPlayViewModel.kt"],
                "backend_event": "记录导出任务元数据",
                "notes": "可选择 FlowState、防抖、ColorPlus、动态拼接等参数。",
            },
            {
                "order": 2,
                "name": "导出图像/视频",
                "sdk_calls": ["ExportUtils.exportImage(work, params, callback)", "ExportUtils.exportVideo(work, params, callback)"],
                "demo_files": ["ui/play/WorkPlayViewModel.kt"],
                "backend_event": "导出完成后回填报告附件路径",
                "notes": "导出失败返回错误码，用户可取消 ExportUtils.stopExport。",
            },
        ],
    },
    "status": {
        "title": "设备状态刷新",
        "recommended_connection": "BLE/Wi-Fi/USB",
        "backend_handoff": "PATCH /api/health/devices/{device_id}",
        "safety_checks": ["连接类型有效", "错误码转换为用户可读状态", "低电量时暂停自动采集"],
        "steps": [
            {
                "order": 1,
                "name": "刷新状态",
                "sdk_calls": ["fetchCameraOptions(callback)", "onCameraStatusChanged(enabled, connectType)"],
                "demo_files": ["ui/connect/ConnectViewModel.kt", "ui/capture/CaptureViewModel.kt"],
                "backend_event": "更新 online/offline/low_battery/fault",
                "notes": "Wi-Fi 或 USB 断开时停止 ConnectService 并保留缓存。",
            }
        ],
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _demo_reference_path() -> Path:
    configured = settings.insta360_sdk_demo_path.strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (_repo_root().parent / "sdk_demo_1.9.11").resolve()


def get_sdk_status() -> dict[str, Any]:
    demo_path = _demo_reference_path()
    bridge_mode = "native_android_bridge_ready" if settings.insta360_native_bridge_enabled else "contract_only"
    return {
        "provider": PROVIDER_ID,
        "sdk_version": SDK_VERSION,
        "bridge_mode": bridge_mode,
        "native_bridge_available": settings.insta360_native_bridge_enabled,
        "demo_reference": {
            "path": str(demo_path),
            "exists": demo_path.exists(),
            "committed": False,
            "note": "Local SDK demo is used as a reference only and is ignored by git.",
        },
        "features": FEATURES,
        "workflows": list(SUPPORTED_OPERATIONS),
        "integration_notes": [
            "Backend keeps a provider contract and does not import Android SDK classes.",
            "Android bridge should call health APIs with device state, capture metadata, and downloaded media paths.",
            "The vendor demo, APK, signing files, and SDK binaries must remain outside repository history.",
        ],
        "generated_at": now_iso(),
    }


def get_command_plan(operation: str) -> dict[str, Any] | None:
    workflow = WORKFLOWS.get(operation)
    if not workflow:
        return None
    return {
        "operation": operation,
        "provider": PROVIDER_ID,
        "sdk_version": SDK_VERSION,
        "title": workflow["title"],
        "recommended_connection": workflow["recommended_connection"],
        "backend_handoff": workflow["backend_handoff"],
        "safety_checks": workflow["safety_checks"],
        "steps": workflow["steps"],
    }
