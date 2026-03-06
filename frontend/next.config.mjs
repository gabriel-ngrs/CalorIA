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

  // Corrige o file watcher no WSL2 + Docker bind mount.
  // CRÍTICO: `ignored` impede que webpack faça polling em node_modules
  // (milhares de arquivos) a cada tick — principal causa do CPU 140%+.
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 2000,
        aggregateTimeout: 500,
        ignored: ["**/node_modules/**", "**/.git/**", "**/.next/**"],
      };
    }
    return config;
  },
};

export default nextConfig;
