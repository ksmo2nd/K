import Foundation
import NetworkExtension
import UIKit

/**
 * WiFi QR Connector for iOS
 * Handles automatic WiFi connection from QR codes using NEHotspotConfiguration
 */
class WiFiQRConnector: NSObject {
    
    // MARK: - Properties
    static let shared = WiFiQRConnector()
    private let baseURL = "https://kswifi.onrender.com/api"
    
    // MARK: - Public Methods
    
    /**
     * Connect to WiFi network from QR code data
     * @param qrString: WiFi QR format string (WIFI:T:WPA;S:network;P:password;H:false;;)
     * @param completion: Callback with success/error result
     */
    func connectFromQR(_ qrString: String, completion: @escaping (Result<String, Error>) -> Void) {
        
        print("📱 WiFi QR: Parsing QR code data...")
        
        // Parse WiFi QR format
        guard let wifiConfig = parseWiFiQR(qrString) else {
            completion(.failure(WiFiError.invalidQRFormat))
            return
        }
        
        print("📶 WiFi QR: Connecting to network \(wifiConfig.ssid)")
        
        // Create NEHotspotConfiguration
        let hotspotConfig = NEHotspotConfiguration(
            ssid: wifiConfig.ssid,
            passphrase: wifiConfig.password,
            isWEP: false
        )
        
        // Remove previous configurations to avoid conflicts
        hotspotConfig.lifeTimeInDays = 1
        
        // Apply WiFi configuration
        NEHotspotConfigurationManager.shared.apply(hotspotConfig) { [weak self] error in
            DispatchQueue.main.async {
                if let error = error {
                    print("❌ WiFi Connection Error: \(error.localizedDescription)")
                    completion(.failure(error))
                } else {
                    print("✅ WiFi Connected Successfully!")
                    
                    // Validate session with server
                    self?.validateSession(networkName: wifiConfig.ssid) { result in
                        switch result {
                        case .success(let message):
                            completion(.success(message))
                        case .failure(let error):
                            completion(.failure(error))
                        }
                    }
                }
            }
        }
    }
    
    /**
     * Get device MAC address for session validation
     */
    func getDeviceMACAddress() -> String {
        // iOS doesn't allow direct MAC address access for privacy
        // Use device identifier instead
        return UIDevice.current.identifierForVendor?.uuidString ?? "unknown-device"
    }
    
    // MARK: - Private Methods
    
    /**
     * Parse WiFi QR code format
     * Format: WIFI:T:WPA;S:network_name;P:password;H:false;;
     */
    private func parseWiFiQR(_ qrString: String) -> WiFiConfig? {
        
        // Validate format
        guard qrString.hasPrefix("WIFI:") && qrString.hasSuffix(";;") else {
            print("❌ Invalid WiFi QR format")
            return nil
        }
        
        // Remove WIFI: prefix and ;; suffix
        let content = String(qrString.dropFirst(5).dropLast(2))
        let components = content.components(separatedBy: ";")
        
        var ssid: String?
        var password: String?
        var security: String?
        
        for component in components {
            if component.hasPrefix("S:") {
                ssid = String(component.dropFirst(2))
            } else if component.hasPrefix("P:") {
                password = String(component.dropFirst(2))
            } else if component.hasPrefix("T:") {
                security = String(component.dropFirst(2))
            }
        }
        
        guard let networkSSID = ssid,
              let networkPassword = password else {
            print("❌ Missing SSID or password in QR code")
            return nil
        }
        
        print("✅ Parsed WiFi QR: SSID=\(networkSSID), Security=\(security ?? "WPA")")
        
        return WiFiConfig(
            ssid: networkSSID,
            password: networkPassword,
            security: security ?? "WPA"
        )
    }
    
    /**
     * Validate session with KSWiFi server
     */
    private func validateSession(networkName: String, completion: @escaping (Result<String, Error>) -> Void) {
        
        print("🔐 Validating session with server...")
        
        guard let url = URL(string: "\(baseURL)/wifi/validate-connection") else {
            completion(.failure(WiFiError.invalidURL))
            return
        }
        
        let requestBody: [String: Any] = [
            "network_name": networkName,
            "device_mac": getDeviceMACAddress()
        ]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                
                if let error = error {
                    print("❌ Session validation network error: \(error)")
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(WiFiError.noData))
                    return
                }
                
                do {
                    let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                    
                    if let success = json?["success"] as? Bool, success {
                        print("✅ Session validated successfully!")
                        let message = json?["message"] as? String ?? "Internet access granted"
                        completion(.success(message))
                    } else {
                        let errorMessage = json?["error"] as? String ?? "Session validation failed"
                        completion(.failure(WiFiError.validationFailed(errorMessage)))
                    }
                    
                } catch {
                    completion(.failure(error))
                }
            }
        }.resume()
    }
}

// MARK: - Supporting Types

struct WiFiConfig {
    let ssid: String
    let password: String
    let security: String
}

enum WiFiError: LocalizedError {
    case invalidQRFormat
    case invalidURL
    case noData
    case validationFailed(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidQRFormat:
            return "Invalid WiFi QR code format"
        case .invalidURL:
            return "Invalid server URL"
        case .noData:
            return "No response data from server"
        case .validationFailed(let message):
            return "Session validation failed: \(message)"
        }
    }
}

// MARK: - Usage Example

/*
// Example usage in your iOS app:

import AVFoundation

class QRScannerViewController: UIViewController {
    
    func didScanQRCode(_ qrString: String) {
        
        // Show loading indicator
        showLoadingIndicator("Connecting to WiFi...")
        
        // Connect to WiFi using QR code
        WiFiQRConnector.shared.connectFromQR(qrString) { [weak self] result in
            
            DispatchQueue.main.async {
                self?.hideLoadingIndicator()
                
                switch result {
                case .success(let message):
                    // Success - show confirmation
                    self?.showSuccessAlert(
                        title: "Connected!",
                        message: message
                    )
                    
                case .failure(let error):
                    // Error - show error message
                    self?.showErrorAlert(
                        title: "Connection Failed",
                        message: error.localizedDescription
                    )
                }
            }
        }
    }
}
*/