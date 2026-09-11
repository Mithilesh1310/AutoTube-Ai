/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  ...(process.env.DOCKER_BUILD ? { output: 'standalone' } : {}),
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/storage/:path*',
        destination: 'http://localhost:8000/storage/:path*',
      },
    ];
  },
};

export default nextConfig;
