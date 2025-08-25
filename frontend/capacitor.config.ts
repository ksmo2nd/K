import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.kswifi.app',
  appName: 'KSWiFi',
  webDir: 'frontend/out',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: "#000000",
      androidSplashResourceName: "splash",
      androidScaleType: "CENTER_CROP",
      showSpinner: true,
      androidSpinnerStyle: "large",
      iosSpinnerStyle: "small",
      spinnerColor: "#00CFE8",
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#000000',
    },
    Keyboard: {
      resize: 'body',
      style: 'DARK',
      resizeOnFullScreen: true,
    },
    App: {
      faceId: false,
      touchId: false,
    },
    Geolocation: {
      permissions: {
        "android.permission.ACCESS_COARSE_LOCATION": "This app needs location permission to detect WiFi networks.",
        "android.permission.ACCESS_FINE_LOCATION": "This app needs location permission to detect WiFi networks."
      }
    },
    Device: {
      permissions: {
        "android.permission.READ_PHONE_STATE": "This app needs device information for eSIM management."
      }
    },
    LocalNotifications: {
      smallIcon: "ic_stat_icon_config_sample",
      iconColor: "#00CFE8",
      sound: "beep.wav",
    },
    Network: {
      permissions: {
        "android.permission.ACCESS_NETWORK_STATE": "This app needs network access to manage WiFi and eSIM connections.",
        "android.permission.CHANGE_NETWORK_STATE": "This app needs to change network settings for eSIM activation."
      }
    }
  },
  ios: {
    contentInset: 'automatic',
    backgroundColor: '#000000',
    allowsLinkPreview: false,
    handleApplicationNotifications: true,
  },
  android: {
    backgroundColor: '#000000',
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: false,
    appendUserAgent: 'KSWiFi-App',
    overrideUserAgent: 'KSWiFi-App Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36',
    useLegacyBridge: false,
  }
};

export default config;