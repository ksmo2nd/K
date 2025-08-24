/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for Capacitor
  output: 'export',
  
  // Disable image optimization for static export
  images: {
    unoptimized: true
  },
  
  // Remove trailing slash to prevent routing issues
  trailingSlash: false,
  
  // Base path configuration for different environments
  basePath: process.env.NODE_ENV === 'production' ? '' : '',
  
  // Asset prefix for CDN or static hosting
  assetPrefix: process.env.NODE_ENV === 'production' ? '' : '',
  
  // Experimental features for better mobile performance
  experimental: {
    optimizeCss: true,
    scrollRestoration: true,
  },
  
  // Compiler options for better performance
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Headers for better security and performance
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },
  
  // Webpack configuration for better mobile performance
  webpack: (config, { isServer }) => {
    // Optimize for mobile
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
            reuseExistingChunk: true,
          },
        },
      }
      
      // Enable tree shaking
      config.optimization.usedExports = true
      config.optimization.sideEffects = false
    }
    
    return config
  },
}

module.exports = nextConfig