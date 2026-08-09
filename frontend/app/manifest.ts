import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "CalorIA — Diário Alimentar",
    short_name: "CalorIA",
    description: "Diário alimentar inteligente com IA",
    start_url: "/dashboard",
    display: "standalone",
    // Espelham o design system atual (`app/globals.css`): `--background` do
    // light mode e `--primary`. Os valores anteriores (#1a2a30 / #527787) eram
    // de uma paleta descontinuada e destoavam do app instalado.
    background_color: "#EAEEF4",
    theme_color: "#10B981",
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
