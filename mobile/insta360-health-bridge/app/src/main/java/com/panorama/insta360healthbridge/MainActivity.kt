package com.panorama.insta360healthbridge

import android.Manifest
import android.app.Activity
import android.os.Build
import android.os.Bundle
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var apiInput: EditText
    private lateinit var sceneInput: EditText
    private lateinit var logView: TextView
    private lateinit var apiClient: HealthApiClient
    private lateinit var controller: Insta360BridgeController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestBridgePermissions()
        apiClient = HealthApiClient("http://10.0.2.2:8010", ::appendLog)
        controller = Insta360BridgeController(this, apiClient, ::appendLog)
        setContentView(createContentView())
    }

    override fun onDestroy() {
        controller.release()
        super.onDestroy()
    }

    private fun createContentView(): ScrollView {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 28, 28, 28)
        }
        apiInput = EditText(this).apply {
            setText("http://10.0.2.2:8010")
            hint = "API base URL"
        }
        sceneInput = EditText(this).apply {
            setText("breakfast")
            hint = "Scene hint"
        }
        logView = TextView(this).apply {
            textSize = 13f
            text = "Ready.\n"
        }
        root.addView(title("Insta360 Health Bridge"))
        root.addView(apiInput)
        root.addView(sceneInput)
        root.addView(button("Scan BLE") { updateConfig(); controller.scanBleAndConnect() })
        root.addView(button("Connect USB") { updateConfig(); controller.connectUsb() })
        root.addView(button("Connect Wi-Fi") { updateConfig(); controller.connectWifi() })
        root.addView(button("Push Status") { updateConfig(); controller.pushStatus() })
        root.addView(button("Capture") { updateConfig(); controller.capture() })
        root.addView(button("Disconnect") { controller.disconnect() })
        root.addView(logView)
        return ScrollView(this).apply { addView(root) }
    }

    private fun updateConfig() {
        apiClient.updateBaseUrl(apiInput.text.toString())
        controller.sceneHint = sceneInput.text.toString().ifBlank { "breakfast" }
    }

    private fun title(value: String) = TextView(this).apply {
        text = value
        textSize = 22f
        setPadding(0, 0, 0, 18)
    }

    private fun button(label: String, onClick: () -> Unit) = Button(this).apply {
        text = label
        layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        setOnClickListener { onClick() }
    }

    private fun appendLog(message: String) {
        runOnUiThread {
            logView.append("$message\n")
        }
    }

    private fun requestBridgePermissions() {
        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions += Manifest.permission.BLUETOOTH_SCAN
            permissions += Manifest.permission.BLUETOOTH_CONNECT
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions += Manifest.permission.READ_MEDIA_IMAGES
            permissions += Manifest.permission.READ_MEDIA_VIDEO
        }
        requestPermissions(permissions.toTypedArray(), 1001)
    }
}
