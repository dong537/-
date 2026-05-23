# 影石 Insta360 SDK 接入说明

## 本地 demo 使用规则

影石 SDK demo 位于本机：

```text
C:\Users\Lenovo\Desktop\黑客松prd\sdk_demo_1.9.11
```

该目录只作为本地参考，不提交到 GitHub。仓库已在 `.gitignore` 增加 `sdk_demo_1.9.11/`、`*.apk`、`*.aab`，避免误把厂商 demo、APK、签名文件或 SDK 二进制加入版本历史。

如需让后端运行时显示 demo 路径，可配置：

```powershell
$env:INSTA360_SDK_DEMO_PATH="C:\Users\Lenovo\Desktop\黑客松prd\sdk_demo_1.9.11"
```

## 当前接入方式

本项目当前实现的是可提交的 SDK bridge contract：

- 后端不导入 Android SDK 类，不复制 demo 源码。
- Android 原生桥接层负责调用影石 SDK，并把设备状态、采集元数据、下载后的文件路径回传到健康监测 API。
- FastAPI 保持 provider-agnostic，只消费设备、影像和同步结果。
- 真实设备桥接工程位于 `mobile/insta360-health-bridge`，可用 Android Studio 打开并安装到安卓手机。

已新增接口：

```text
GET /api/health/insta360/sdk/status
GET /api/health/insta360/sdk/command-plan?operation=bind|capture|sync|export|status
POST /api/health/insta360/bridge/devices
POST /api/health/insta360/bridge/devices/{device_id}/status
POST /api/health/insta360/bridge/captures
POST /api/health/insta360/bridge/captures/upload
```

provider 标识：

```text
insta360_android_sdk_v1_9_11_bridge
```

## Demo 关键文件映射

| Demo 文件 | SDK 能力 | 项目映射 |
| --- | --- | --- |
| `InstaApp.kt` | `UsbMgr.init`、`InstaCameraSDK.init`、`InstaMediaSDK.init`、日志初始化 | Android App 启动时初始化 SDK，后端记录 bridge 状态 |
| `ui/connect/ConnectViewModel.kt` | BLE 扫描、BLE 连接、Wi-Fi/USB 打开相机、网络绑定 | 设备发现、绑定、在线状态、电量/容量同步 |
| `service/ConnectService.java` | 连接保活服务 | Wi-Fi/USB 连接期间保持前台服务 |
| `ui/capture/CaptureViewModel.kt` | 预览流、能力读取、参数下发、抓拍/录制/间隔拍摄 | 手动抓拍、自动采集、离线缓存采集 |
| `capture/CameraOfflineData.kt` | 离线参数缓存 | 采集配置和相机参数回放 |
| `ui/album/AlbumViewModel.kt` | `WorkUtils` 相机作品列表、本地作品、下载、删除 | 离线缓存同步和素材入库 |
| `ui/play/WorkPlayViewModel.kt` | 播放参数、HDR/PureShot、图片/视频导出 | 报告附件、媒体分析输入和后续出片 |

## 桥接流程

绑定流程：

```text
InstaCameraSDK.init / InstaMediaSDK.init
  -> setScanBleListener + startBleScan
  -> connectBle 或 openCamera(WIFI/USB)
  -> fetchCameraOptions
  -> POST /api/health/devices/bind
```

采集流程：

```text
fetchCameraOptions + initCameraSupportConfig
  -> startPreviewStream
  -> startNormalCapture / startIntervalShooting / startNormalRecord
  -> onCaptureFinish(paths)
  -> POST /api/health/captures
```

同步流程：

```text
WorkUtils.getAllCameraWorks
  -> OkGo 下载相机文件
  -> POST /api/health/devices/{device_id}/sync
  -> AI 行为分析与日报/周报更新
```

## Android 侧建议边界

建议后续新增独立 Android 模块或 App bridge，而不是把 demo 直接复制进仓库：

```text
mobile/
  app/
    src/main/java/.../Insta360HealthBridge.kt
```

桥接层建议输出统一事件：

```json
{
  "device_id": "device_xxx",
  "provider": "insta360_android_sdk_v1_9_11_bridge",
  "connection_type": "wifi",
  "status": "online",
  "battery_percent": 86,
  "storage_free_gb": 58.4,
  "capture": {
    "capture_mode": "auto",
    "image_url": "/files/health-demo/xxx.jpg",
    "captured_at": "2026-05-23T10:00:00+08:00"
  }
}
```

## 真实设备步骤

1. 运行 `.\scripts\stop-dev.ps1`，再运行 `.\scripts\start-real-device.ps1`。
2. 记下脚本输出的 `API for Android phone` 地址。
3. 用 Android Studio 打开 `mobile/insta360-health-bridge`，配置影石 Maven 凭据后安装到安卓手机。
4. 手机与电脑连接同一 Wi-Fi，在 App 中填入第 2 步的 API 地址。
5. 打开相机并确保手机蓝牙、定位、Wi-Fi 权限已授权。
6. 优先点 `Scan BLE`，发现设备后自动 BLE 连接；如使用 USB 线，点 `Connect USB`。
7. 连接成功后点 `Capture`，后端 Web 工作台会出现真实设备采集记录。

## 验证

```powershell
.\scripts\test-api.ps1
node .\node_modules\typescript\bin\tsc -b --pretty false
node .\node_modules\vite\bin\vite.js build --clearScreen false
```
