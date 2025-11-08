/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      allowedOrigins: ["agentic-5f2e9c6e.vercel.app", "localhost:3000"],
      bodySizeLimit: "2mb"
    }
  }
};

export default nextConfig;
