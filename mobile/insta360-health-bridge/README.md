# Insta360 Health Bridge Android

这是给真实影石设备使用的 Android bridge 骨架。它不复制 `sdk_demo_1.9.11`，只按影石 SDK 的 Maven 依赖接入 `sdkcamera` / `sdkmedia`，并把真实设备状态、抓拍结果和上传文件回传到 Panorama Companion API。

## 运行前准备

1. 用 Android Studio 打开本目录。
2. 配置影石 Maven 凭据，建议放在用户级 `~/.gradle/gradle.properties`，不要提交到仓库：

```properties
INSTA360_MAVEN_USERNAME=your_username
INSTA360_MAVEN_PASSWORD=your_password
```

3. 真实手机接入时，先用局域网模式启动后端：

```powershell
.\scripts\stop-dev.ps1
.\scripts\start-real-device.ps1
```

4. 手机和电脑在同一个 Wi-Fi 下时，把 App 里的 API 地址改成脚本输出的局域网地址，例如：

```text
http://192.168.1.10:8010
```

Android 模拟器访问电脑可用默认值：

```text
http://10.0.2.2:8010
```

## 已接入能力

- 初始化 `InstaCameraSDK` / `InstaMediaSDK`
- BLE 扫描并自动连接首个发现设备
- USB / Wi-Fi 打开相机
- 相机连接、电量、容量、版本、序列号回传到：

```text
POST /api/health/insta360/bridge/devices
POST /api/health/insta360/bridge/devices/{device_id}/status
```

- 普通抓拍，若 SDK 返回本地文件路径则上传文件；否则提交相机侧文件 URL 元数据：

```text
POST /api/health/insta360/bridge/captures
POST /api/health/insta360/bridge/captures/upload
```

## 真实设备步骤

1. 打开相机并确保手机蓝牙、定位、Wi-Fi 权限已授权。
2. 优先点 `Scan BLE`，发现设备后自动 BLE 连接，并根据 SDK 返回的 Wi-Fi 信息继续连接。
3. 如使用 USB 线，点 `Connect USB`。
4. 连接成功后点 `Capture`，后端 Web 工作台会出现真实设备采集记录。

## 说明

这个工程是项目自有桥接层，不是厂商 demo。需要更完整的相册下载、预览流、参数设置时，可继续参照本机 `sdk_demo_1.9.11` 中的 `ConnectViewModel.kt`、`CaptureViewModel.kt` 和 `AlbumViewModel.kt` 扩展。
