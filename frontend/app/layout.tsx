import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "@/components/ui/sonner";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

// Roda antes do primeiro paint, síncrono e sem depender de React. O `try` cobre
// navegador com localStorage bloqueado, onde ler já lança.
const THEME_NO_FLASH_SCRIPT = `try{var t=localStorage.getItem("caloria-theme");if(t==="dark"){document.documentElement.classList.add("dark")}}catch(e){}`;

const SITE_DESCRIPTION =
  "Diário alimentar inteligente: registre a refeição por texto ou foto e a IA analisa os macronutrientes.";

// Sem `metadataBase` o build emite warning e toda URL relativa de OpenGraph
// resolve errado quando o link é compartilhado. `NEXT_PUBLIC_SITE_URL` permite
// apontar para o domínio real sem novo código.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "CalorIA — Diário alimentar inteligente",
    template: "%s · CalorIA",
  },
  description: SITE_DESCRIPTION,
  applicationName: "CalorIA",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    siteName: "CalorIA",
    title: "CalorIA — Diário alimentar inteligente",
    description: SITE_DESCRIPTION,
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title: "CalorIA — Diário alimentar inteligente",
    description: SITE_DESCRIPTION,
  },
  appleWebApp: {
    statusBarStyle: "default",
    title: "CalorIA",
  },
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        {/* Aplica o tema salvo ANTES do primeiro paint. O ThemeProvider roda
            dentro de useEffect, depois da hidratação, então quem tinha tema
            escuro salvo via um flash claro a cada carregamento. */}
        <script
          dangerouslySetInnerHTML={{ __html: THEME_NO_FLASH_SCRIPT }}
        />
      </head>
      <body className={spaceGrotesk.className}>
        <Providers>{children}</Providers>
        <Toaster richColors position="bottom-right" />
      </body>
    </html>
  );
}
