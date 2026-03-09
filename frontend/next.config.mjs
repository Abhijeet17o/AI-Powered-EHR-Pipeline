/** @type {import('next').NextConfig} */

// Supports local dev (127.0.0.1:5000) and Docker (BACKEND_URL=http://backend:5000)
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:5000';

const nextConfig = {
  // Proxy API calls to Flask backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/new_patient',
        destination: `${BACKEND_URL}/new_patient`,
      },
      {
        source: '/update_patient/:path*',
        destination: `${BACKEND_URL}/update_patient/:path*`,
      },
      {
        source: '/process_consultation/:path*',
        destination: `${BACKEND_URL}/process_consultation/:path*`,
      },
      {
        source: '/save_prescription/:path*',
        destination: `${BACKEND_URL}/save_prescription/:path*`,
      },
      {
        source: '/search_medicine',
        destination: `${BACKEND_URL}/search_medicine`,
      },
      {
        source: '/add_medicine',
        destination: `${BACKEND_URL}/add_medicine`,
      },
      {
        source: '/update_medicine/:path*',
        destination: `${BACKEND_URL}/update_medicine/:path*`,
      },
      {
        source: '/delete_medicine/:path*',
        destination: `${BACKEND_URL}/delete_medicine/:path*`,
      },
    ];
  },
};

export default nextConfig;
