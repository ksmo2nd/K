package com.kswifi.android

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.WifiConfiguration
import android.net.wifi.WifiManager
import android.net.wifi.WifiNetworkSpecifier
import android.net.ConnectivityManager
import android.net.NetworkRequest
import android.net.NetworkCallback
import android.net.Network
import android.os.Build
import android.provider.Settings
import androidx.core.app.ActivityCompat
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

/**
 * WiFi QR Connector for Android
 * Handles automatic WiFi connection from QR codes using WifiManager
 */
class WiFiQRConnector(private val context: Context) {
    
    companion object {
        private const val BASE_URL = "https://kswifi.onrender.com/api"
        private const val TIMEOUT_SECONDS = 30L
    }
    
    private val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    private val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(TIMEOUT_SECONDS, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(TIMEOUT_SECONDS, java.util.concurrent.TimeUnit.SECONDS)
        .build()
    
    /**
     * Connect to WiFi network from QR code data
     * @param qrString WiFi QR format string (WIFI:T:WPA;S:network;P:password;H:false;;)
     * @param callback Callback with success/error result
     */
    fun connectFromQR(qrString: String, callback: (Result<String>) -> Unit) {
        
        println("📱 WiFi QR: Parsing QR code data...")
        
        // Parse WiFi QR format
        val wifiConfig = parseWiFiQR(qrString)
        if (wifiConfig == null) {
            callback(Result.failure(Exception("Invalid WiFi QR code format")))
            return
        }
        
        println("📶 WiFi QR: Connecting to network ${wifiConfig.ssid}")
        
        // Check permissions
        if (!hasWiFiPermissions()) {
            callback(Result.failure(Exception("WiFi permissions not granted")))
            return
        }
        
        // Connect based on Android version
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            connectToWiFiModern(wifiConfig, callback)
        } else {
            connectToWiFiLegacy(wifiConfig, callback)
        }
    }
    
    /**
     * Get device MAC address for session validation
     * Note: Android 6+ restricts MAC address access
     */
    fun getDeviceMACAddress(): String {
        return try {
            Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown-device"
        } catch (e: Exception) {
            "unknown-device"
        }
    }
    
    // MARK: - Private Methods
    
    /**
     * Parse WiFi QR code format
     * Format: WIFI:T:WPA;S:network_name;P:password;H:false;;
     */
    private fun parseWiFiQR(qrString: String): WiFiConfig? {
        
        // Validate format
        if (!qrString.startsWith("WIFI:") || !qrString.endsWith(";;")) {
            println("❌ Invalid WiFi QR format")
            return null
        }
        
        // Remove WIFI: prefix and ;; suffix
        val content = qrString.substring(5, qrString.length - 2)
        val components = content.split(";")
        
        var ssid: String? = null
        var password: String? = null
        var security: String? = null
        
        for (component in components) {
            when {
                component.startsWith("S:") -> ssid = component.substring(2)
                component.startsWith("P:") -> password = component.substring(2)
                component.startsWith("T:") -> security = component.substring(2)
            }
        }
        
        if (ssid.isNullOrEmpty() || password.isNullOrEmpty()) {
            println("❌ Missing SSID or password in QR code")
            return null
        }
        
        println("✅ Parsed WiFi QR: SSID=$ssid, Security=${security ?: "WPA"}")
        
        return WiFiConfig(
            ssid = ssid,
            password = password,
            security = security ?: "WPA"
        )
    }
    
    /**
     * Connect to WiFi on Android 10+ using WifiNetworkSpecifier
     */
    @Suppress("NewApi")
    private fun connectToWiFiModern(wifiConfig: WiFiConfig, callback: (Result<String>) -> Unit) {
        
        val specifier = WifiNetworkSpecifier.Builder()
            .setSsid(wifiConfig.ssid)
            .setWpa2Passphrase(wifiConfig.password)
            .build()
        
        val networkRequest = NetworkRequest.Builder()
            .addTransportType(android.net.NetworkCapabilities.TRANSPORT_WIFI)
            .setNetworkSpecifier(specifier)
            .build()
        
        val networkCallback = object : NetworkCallback() {
            override fun onAvailable(network: Network) {
                super.onAvailable(network)
                println("✅ WiFi Connected Successfully!")
                
                // Validate session with server
                validateSession(wifiConfig.ssid) { result ->
                    when {
                        result.isSuccess -> callback(Result.success(result.getOrNull() ?: "Connected"))
                        else -> callback(Result.failure(result.exceptionOrNull() ?: Exception("Validation failed")))
                    }
                }
            }
            
            override fun onUnavailable() {
                super.onUnavailable()
                println("❌ WiFi Connection Failed: Network unavailable")
                callback(Result.failure(Exception("WiFi network unavailable")))
            }
        }
        
        connectivityManager.requestNetwork(networkRequest, networkCallback)
        
        // Set timeout
        CoroutineScope(Dispatchers.Main).launch {
            delay(TIMEOUT_SECONDS * 1000)
            connectivityManager.unregisterNetworkCallback(networkCallback)
        }
    }
    
    /**
     * Connect to WiFi on Android 9 and below using WifiManager
     */
    @Suppress("DEPRECATION")
    private fun connectToWiFiLegacy(wifiConfig: WiFiConfig, callback: (Result<String>) -> Unit) {
        
        val wifiConfiguration = WifiConfiguration().apply {
            SSID = "\"${wifiConfig.ssid}\""
            preSharedKey = "\"${wifiConfig.password}\""
            allowedKeyManagement.set(WifiConfiguration.KeyMgmt.WPA_PSK)
        }
        
        // Add network configuration
        val networkId = wifiManager.addNetwork(wifiConfiguration)
        
        if (networkId == -1) {
            callback(Result.failure(Exception("Failed to add WiFi network configuration")))
            return
        }
        
        // Enable and connect to network
        val connected = wifiManager.enableNetwork(networkId, true) && wifiManager.reconnect()
        
        if (connected) {
            println("✅ WiFi Connected Successfully!")
            
            // Validate session with server
            validateSession(wifiConfig.ssid) { result ->
                when {
                    result.isSuccess -> callback(Result.success(result.getOrNull() ?: "Connected"))
                    else -> callback(Result.failure(result.exceptionOrNull() ?: Exception("Validation failed")))
                }
            }
        } else {
            callback(Result.failure(Exception("Failed to connect to WiFi network")))
        }
    }
    
    /**
     * Validate session with KSWiFi server
     */
    private fun validateSession(networkName: String, callback: (Result<String>) -> Unit) {
        
        println("🔐 Validating session with server...")
        
        val json = JSONObject().apply {
            put("network_name", networkName)
            put("device_mac", getDeviceMACAddress())
        }
        
        val requestBody = json.toString().toRequestBody("application/json".toMediaType())
        
        val request = Request.Builder()
            .url("$BASE_URL/wifi/validate-connection")
            .post(requestBody)
            .build()
        
        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                println("❌ Session validation network error: ${e.message}")
                callback(Result.failure(e))
            }
            
            override fun onResponse(call: Call, response: Response) {
                response.use { 
                    try {
                        val responseBody = it.body?.string() ?: ""
                        val jsonResponse = JSONObject(responseBody)
                        
                        val success = jsonResponse.optBoolean("success", false)
                        
                        if (success) {
                            println("✅ Session validated successfully!")
                            val message = jsonResponse.optString("message", "Internet access granted")
                            callback(Result.success(message))
                        } else {
                            val errorMessage = jsonResponse.optString("error", "Session validation failed")
                            callback(Result.failure(Exception("Validation failed: $errorMessage")))
                        }
                        
                    } catch (e: Exception) {
                        callback(Result.failure(e))
                    }
                }
            }
        })
    }
    
    /**
     * Check if app has necessary WiFi permissions
     */
    private fun hasWiFiPermissions(): Boolean {
        return when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q -> {
                // Android 10+ requires ACCESS_FINE_LOCATION for WiFi operations
                ActivityCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            }
            else -> {
                // Pre-Android 10 requires ACCESS_WIFI_STATE and CHANGE_WIFI_STATE
                ActivityCompat.checkSelfPermission(context, Manifest.permission.ACCESS_WIFI_STATE) == PackageManager.PERMISSION_GRANTED &&
                ActivityCompat.checkSelfPermission(context, Manifest.permission.CHANGE_WIFI_STATE) == PackageManager.PERMISSION_GRANTED
            }
        }
    }
}

// MARK: - Supporting Types

data class WiFiConfig(
    val ssid: String,
    val password: String,
    val security: String
)

// MARK: - Usage Example

/*
// Example usage in your Android app:

class QRScannerActivity : AppCompatActivity() {
    
    private lateinit var wifiConnector: WiFiQRConnector
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        wifiConnector = WiFiQRConnector(this)
    }
    
    fun onQRCodeScanned(qrString: String) {
        
        // Show loading indicator
        showLoadingDialog("Connecting to WiFi...")
        
        // Connect to WiFi using QR code
        wifiConnector.connectFromQR(qrString) { result ->
            
            runOnUiThread {
                hideLoadingDialog()
                
                when {
                    result.isSuccess -> {
                        // Success - show confirmation
                        showSuccessDialog(
                            title = "Connected!",
                            message = result.getOrNull() ?: "WiFi connected successfully"
                        )
                    }
                    
                    result.isFailure -> {
                        // Error - show error message
                        showErrorDialog(
                            title = "Connection Failed",
                            message = result.exceptionOrNull()?.message ?: "Unknown error"
                        )
                    }
                }
            }
        }
    }
    
    // Request permissions if needed
    private fun requestWiFiPermissions() {
        val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        } else {
            arrayOf(
                Manifest.permission.ACCESS_WIFI_STATE,
                Manifest.permission.CHANGE_WIFI_STATE
            )
        }
        
        ActivityCompat.requestPermissions(this, permissions, WIFI_PERMISSION_REQUEST_CODE)
    }
    
    companion object {
        private const val WIFI_PERMISSION_REQUEST_CODE = 1001
    }
}
*/