import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.kswifi.app',
  appName: 'KSWiFi',
  webDir: 'frontend/out',
  server: {
    androidScheme: 'https',
    iosScheme: 'https',
    url: process.env.NODE_ENV === 'development' 
      ? 'http://localhost:3000'
      : 'https://kswifi.app'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 3000,
      backgroundColor: "#ffffffff",
      androidSplashResourceName: "splash",
      androidScaleType: "CENTER_CROP",
      showSpinner: true,
      androidSpinnerStyle: "large",
      iosSpinnerStyle: "small",
      spinnerColor: "#999999",
      splashFullScreen: true,
      splashImmersive: true,
    },
  },
};

export default config;
