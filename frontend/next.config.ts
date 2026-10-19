import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  // Keep a running development server separate from production build output.
  distDir: process.env.NEXT_DIST_DIR || (process.env.NODE_ENV === "development" ? ".next-dev" : ".next"),
  typescript: { tsconfigPath: process.env.NEXT_DIST_DIR === ".next-test" ? "tsconfig.playwright.json" : "tsconfig.json" },
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    ] }];
  },
};
export default nextConfig;
