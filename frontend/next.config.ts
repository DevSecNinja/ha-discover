import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Set basePath for GitHub Pages (repo name)
  basePath: '/ha-discover',
};

export default nextConfig;
