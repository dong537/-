package com.panorama.insta360healthbridge

import android.content.Context
import com.arashivision.sdkcamera.camera.InstaCameraManager
import com.arashivision.sdkcamera.camera.callback.ICameraChangedCallback
import com.arashivision.sdkcamera.camera.callback.ICaptureStatusListener
import com.arashivision.sdkcamera.camera.callback.IScanBleListener
import com.clj.fastble.data.BleDevice
import java.io.File

class Insta360BridgeController(
    context: Context,
    private val apiClient: HealthApiClient,
    private val onLog: (String) -> Unit,
) : ICameraChangedCallback, ICaptureStatusListener {
    private val appContext = context.applicationContext
    private val camera = InstaCameraManager.getInstance()
    private var deviceId: String? = null
    private var lastConnectionType = "wifi"
    var sceneHint: String = "breakfast"

    init {
        camera.registerCameraChangedCallback(this)
        camera.setCaptureStatusListener(this)
    }

    fun release() {
        camera.setScanBleListener(null)
        camera.setCaptureStatusListener(null)
        camera.unregisterCameraChangedCallback(this)
    }

    fun scanBleAndConnect() {
        onLog("Start BLE scan")
        camera.setScanBleListener(object : IScanBleListener {
            override fun onScanStartSuccess() = onLog("BLE scan started")
            override fun onScanStartFail() = onLog("BLE scan failed")

            override fun onScanning(bleDevice: BleDevice) {
                onLog("Found ${bleDevice.name}; connecting BLE")
                camera.stopBleScan()
                lastConnectionType = "bluetooth"
                camera.connectBle(bleDevice)
            }

            override fun onScanFinish(list: List<BleDevice>) {
                onLog("BLE scan finished: ${list.size} device(s)")
                camera.stopBleScan()
            }
        })
        camera.startBleScan()
    }

    fun connectUsb() {
        lastConnectionType = "usb"
        onLog("Open camera by USB")
        camera.openCamera(InstaCameraManager.CONNECT_TYPE_USB)
    }

    fun connectWifi() {
        lastConnectionType = "wifi"
        onLog("Open camera by Wi-Fi")
        camera.openCamera(InstaCameraManager.CONNECT_TYPE_WIFI)
    }

    fun disconnect() {
        onLog("Close camera")
        camera.closeCamera()
    }

    fun capture() {
        if (!camera.isSdCardEnabled) {
            onLog("SD card is not available")
            return
        }
        onLog("Start normal capture")
        camera.startNormalCapture()
    }

    fun pushStatus() {
        val currentDeviceId = deviceId
        if (currentDeviceId == null) {
            registerDevice()
        } else {
            apiClient.postStatus(currentDeviceId, currentStatusPayload("online"))
        }
    }

    override fun onCameraStatusChanged(enabled: Boolean, connectType: Int) {
        lastConnectionType = when (connectType) {
            InstaCameraManager.CONNECT_TYPE_USB -> "usb"
            InstaCameraManager.CONNECT_TYPE_BLE -> "bluetooth"
            else -> "wifi"
        }
        onLog("Camera status changed: enabled=$enabled type=$lastConnectionType")
        if (enabled) registerDevice() else deviceId?.let { apiClient.postStatus(it, currentStatusPayload("offline")) }
    }

    override fun onCameraBatteryUpdate(batteryLevel: Int, isCharging: Boolean) {
        onLog("Battery: $batteryLevel% charging=$isCharging")
        pushStatus()
    }

    override fun onCameraStorageChanged(freeSpace: Long, totalSpace: Long) {
        onLog("Storage free: ${bytesToGb(freeSpace)} GB")
        pushStatus()
    }

    override fun onCaptureStarting() = onLog("Capture starting")
    override fun onCaptureWorking() = onLog("Capture working")
    override fun onCaptureStopping() = onLog("Capture stopping")
    override fun onCaptureError(errorCode: Int) = onLog("Capture error: $errorCode")

    override fun onCaptureFinish(paths: Array<String>?) {
        val pathList = paths?.toList().orEmpty()
        onLog("Capture finished: ${pathList.joinToString()}")
        val localFile = pathList.map { File(it) }.firstOrNull { it.exists() && it.isFile }
        if (localFile != null) {
            apiClient.uploadCapture(localFile, "demo_user", deviceId, camera.cameraSerial, sceneHint)
        } else {
            apiClient.postCapture(
                BridgeCapturePayload(
                    userId = "demo_user",
                    deviceId = deviceId,
                    cameraSerial = camera.cameraSerial,
                    sceneHint = sceneHint,
                    localPath = pathList.firstOrNull(),
                    cameraFileUrls = pathList,
                )
            )
        }
    }

    private fun registerDevice() {
        apiClient.registerDevice(currentDevicePayload()) { id ->
            deviceId = id ?: deviceId
            onLog("Bridge device id: ${deviceId ?: "unknown"}")
        }
    }

    private fun currentDevicePayload() = BridgeDevicePayload(
        userId = "demo_user",
        deviceName = camera.cameraType.ifBlank { "Insta360 Camera" },
        deviceModel = camera.cameraType.ifBlank { "Insta360" },
        cameraSerial = camera.cameraSerial,
        cameraVersion = camera.cameraVersion,
        connectionType = lastConnectionType,
        status = "online",
        batteryPercent = camera.cameraCurrentBatteryLevel.coerceIn(0, 100),
        storageFreeGb = bytesToGb(camera.cameraStorageFreeSpace),
    )

    private fun currentStatusPayload(status: String) = BridgeStatusPayload(
        connectionType = lastConnectionType,
        status = status,
        batteryPercent = camera.cameraCurrentBatteryLevel.coerceIn(0, 100),
        storageFreeGb = bytesToGb(camera.cameraStorageFreeSpace),
        cameraVersion = camera.cameraVersion,
    )

    private fun bytesToGb(value: Long): Double =
        String.format("%.2f", value.toDouble() / 1024.0 / 1024.0 / 1024.0).toDouble()
}
