import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Habilita output standalone para Docker multi-stage (menor imagem)
  output: "standalone",
};

export default nextConfig;
