import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "CalorIA — Diário Alimentar",
    short_name: "CalorIA",
    description: "Diário alimentar inteligente com IA",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#1a2a30",
    theme_color: "#527787",
    orientation: "portrait-primary",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "Adicionar refeição",
        short_name: "Refeição",
        description: "Registrar uma nova refeição",
        url: "/refeicoes",
        icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }],
      },
      {
        name: "Registrar água",
        short_name: "Água",
        description: "Registrar consumo de água",
        url: "/hidratacao",
        icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }],
      },
    ],
  };
}
