/** @type {import('next').NextConfig} */
const nextConfig = {
  // Habilita output standalone para Docker multi-stage (menor imagem)
  output: "standalone",

  experimental: {
    // Reduz módulos compilados por rota fazendo tree-shake otimizado das libs pesadas
    // Resultado: hot reload ~30-40% mais rápido em dev
    optimizePackageImports: [
      "lucide-react",
      "recharts",
      "@radix-ui/react-dialog",
      "@radix-ui/react-select",
      "@radix-ui/react-popover",
      "@radix-ui/react-tooltip",
      "@radix-ui/react-dropdown-menu",
      "@tanstack/react-query",
    ],
  },

  // Corrige o file watcher no WSL2 + Docker bind mount
  // inotify não é confiável nesse ambiente — polling evita rebuilds fantasma
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 500,
      };
    }
    return config;
  },
};

export default nextConfig;
