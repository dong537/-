package com.panorama.insta360healthbridge

import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class HealthApiClient(
    @Volatile private var baseUrl: String,
    private val onLog: (String) -> Unit
) {
    fun updateBaseUrl(value: String) {
        baseUrl = value.trimEnd('/')
    }

    fun registerDevice(
        payload: BridgeDevicePayload,
        onDeviceId: (String?) -> Unit
    ) = postJsonAsync("/api/health/insta360/bridge/devices", payload.toJson()) { body ->
        onDeviceId(extractJsonString(body, "device_id"))
    }

    fun postStatus(deviceId: String, payload: BridgeStatusPayload) =
        postJsonAsync("/api/health/insta360/bridge/devices/$deviceId/status", payload.toJson())

    fun postCapture(payload: BridgeCapturePayload) =
        postJsonAsync("/api/health/insta360/bridge/captures", payload.toJson())

    fun uploadCapture(
        file: File,
        userId: String,
        deviceId: String?,
        cameraSerial: String?,
        sceneHint: String
    ) {
        thread(name = "insta360-upload-capture") {
            val boundary = "----PanoramaBoundary${System.currentTimeMillis()}"
            val connection = URL("$baseUrl/api/health/insta360/bridge/captures/upload").openConnection() as HttpURLConnection
            try {
                connection.requestMethod = "POST"
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
                connection.outputStream.use { output ->
                    fun field(name: String, value: String?) {
                        if (value == null) return
                        output.write("--$boundary\r\n".toByteArray())
                        output.write("Content-Disposition: form-data; name=\"$name\"\r\n\r\n".toByteArray())
                        output.write(value.toByteArray())
                        output.write("\r\n".toByteArray())
                    }
                    field("user_id", userId)
                    field("device_id", deviceId)
                    field("camera_serial", cameraSerial)
                    field("capture_mode", "auto")
                    field("scene_hint", sceneHint)
                    output.write("--$boundary\r\n".toByteArray())
                    output.write("Content-Disposition: form-data; name=\"file\"; filename=\"${file.name}\"\r\n".toByteArray())
                    output.write("Content-Type: application/octet-stream\r\n\r\n".toByteArray())
                    file.inputStream().use { input -> input.copyTo(output) }
                    output.write("\r\n--$boundary--\r\n".toByteArray())
                }
                logResponse(connection)
            } catch (error: Exception) {
                onLog("Upload failed: ${error.message}")
            } finally {
                connection.disconnect()
            }
        }
    }

    private fun postJsonAsync(path: String, json: String, onSuccess: (String) -> Unit = {}) {
        thread(name = "insta360-post-json") {
            val connection = URL("$baseUrl$path").openConnection() as HttpURLConnection
            try {
                connection.requestMethod = "POST"
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.use { it.write(json.toByteArray()) }
                val body = logResponse(connection)
                if (connection.responseCode in 200..299) onSuccess(body)
            } catch (error: Exception) {
                onLog("POST $path failed: ${error.message}")
            } finally {
                connection.disconnect()
            }
        }
    }

    private fun logResponse(connection: HttpURLConnection): String {
        val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
        val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
        onLog("HTTP ${connection.responseCode}: $body")
        return body
    }

    private fun extractJsonString(json: String, key: String): String? =
        Regex("\"$key\"\\s*:\\s*\"([^\"]+)\"").find(json)?.groupValues?.getOrNull(1)
}

data class BridgeDevicePayload(
    val userId: String,
    val deviceName: String,
    val deviceModel: String,
    val cameraSerial: String?,
    val cameraVersion: String?,
    val connectionType: String,
    val status: String,
    val batteryPercent: Int,
    val storageFreeGb: Double,
) {
    fun toJson() = """
        {
          "user_id": "${json(userId)}",
          "device_name": "${json(deviceName)}",
          "device_model": "${json(deviceModel)}",
          "camera_serial": ${jsonOrNull(cameraSerial)},
          "camera_version": ${jsonOrNull(cameraVersion)},
          "connection_type": "${json(connectionType)}",
          "status": "${json(status)}",
          "battery_percent": $batteryPercent,
          "storage_free_gb": $storageFreeGb,
          "auto_capture_enabled": true,
          "capture_interval_minutes": 10,
          "capture_window": "08:00-22:00"
        }
    """.trimIndent()
}

data class BridgeStatusPayload(
    val connectionType: String,
    val status: String,
    val batteryPercent: Int,
    val storageFreeGb: Double,
    val cameraVersion: String?,
) {
    fun toJson() = """
        {
          "connection_type": "${json(connectionType)}",
          "status": "${json(status)}",
          "battery_percent": $batteryPercent,
          "storage_free_gb": $storageFreeGb,
          "camera_version": ${jsonOrNull(cameraVersion)}
        }
    """.trimIndent()
}

data class BridgeCapturePayload(
    val userId: String,
    val deviceId: String?,
    val cameraSerial: String?,
    val sceneHint: String,
    val localPath: String?,
    val cameraFileUrls: List<String>,
) {
    fun toJson() = """
        {
          "user_id": "${json(userId)}",
          "device_id": ${jsonOrNull(deviceId)},
          "camera_serial": ${jsonOrNull(cameraSerial)},
          "capture_mode": "auto",
          "scene_hint": "${json(sceneHint)}",
          "local_path": ${jsonOrNull(localPath)},
          "camera_file_urls": [${cameraFileUrls.joinToString(",") { "\"${json(it)}\"" }}]
        }
    """.trimIndent()
}

private fun json(value: String): String =
    value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")

private fun jsonOrNull(value: String?): String =
    value?.let { "\"${json(it)}\"" } ?: "null"
