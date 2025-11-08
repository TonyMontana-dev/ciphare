import { NextConfig } from 'next';

const nextConfig: NextConfig = {
    // For Railway: proxy API requests to Flask backend if NEXT_PUBLIC_API_BASE_URL is set
    ...(process.env.NEXT_PUBLIC_API_BASE_URL && process.env.NODE_ENV === 'production' && {
        rewrites: async () => {
            return [
                {
                    source: '/api/:path*',
                    destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/:path*`,
                },
            ];
        },
    }),
    // For local development
    ...(process.env.NODE_ENV === 'development' && {
        rewrites: async () => {
            return [
                {
                    source: '/api/:path*',
                    destination: 'http://127.0.0.1:5328/api/:path*',
                },
            ];
        },
    }),
    // For Vercel: handled by vercel.json, no rewrites needed
    // For Netlify: handled by netlify.toml redirects
};

export default nextConfig;
