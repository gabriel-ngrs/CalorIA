/** @type {import('next').NextConfig} */
const nextConfig = {
  // Habilita output standalone para Docker multi-stage (menor imagem)
  output: "standalone",

  experimental: {
    // Apenas lucide-react se beneficia desta otimização — é um barrel puro com
    // 1000+ ícones. Outros pacotes (@tanstack, recharts, @radix-ui) não são barrels
    // e quando adicionados aqui AUMENTAM o número de módulos compilados.
    optimizePackageImports: ["lucide-react"],
  },

};

export default nextConfig;
