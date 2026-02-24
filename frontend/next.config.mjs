/** @type {import('next').NextConfig} */
const nextConfig = {
  // Habilita output standalone para Docker multi-stage (menor imagem)
  output: "standalone",
};

export default nextConfig;
