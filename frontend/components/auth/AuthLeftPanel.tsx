"use client";

import { Space_Grotesk } from "next/font/google";
import { Plasma } from "@/components/auth/Plasma";

const sg = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const FEATURES = [
  {
    icon: "🤖",
    accent: "#34d399",
    headline: "IA que realmente entende o que você come",
    body: "Descreva em texto ou mande uma foto. Gemini 2.5 Flash identifica calorias, proteínas, carbs e gorduras na hora.",
    badge: "20 mil+ alimentos",
    badgeColor: "#34d399",
  },
  {
    icon: "📊",
    accent: "#60a5fa",
    headline: "Veja sua evolução, não só o número na balança",
    body: "Peso, hidratação, humor e energia em gráficos limpos. Descubra como sua dieta afeta como você se sente.",
    badge: "Insights diários",
    badgeColor: "#60a5fa",
  },
  {
    icon: "🔔",
    accent: "#fb923c",
    headline: "Lembretes que funcionam, mesmo sem abrir o app",
    body: "Notificações Web Push personalizadas para sua rotina. Você registra, a IA cuida do resto.",
    badge: "100% gratuito",
    badgeColor: "#fb923c",
  },
];

export function AuthLeftPanel() {
  return (
    <div
      className="hidden lg:flex relative flex-col overflow-hidden"
      style={{ width: "48%", minHeight: "100vh" }}
    >
      {/* Gradiente de fundo */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(160deg, #061a10 0%, #0a1628 55%, #050e18 100%)",
        }}
      />

      {/* Plasma suave */}
      <div className="absolute inset-0" style={{ opacity: 0.25 }}>
        <Plasma speed={0.2} scale={1.3} opacity={0.8} />
      </div>

      {/* Glow verde no topo */}
      <div
        className="absolute pointer-events-none"
        style={{
          top: "-10%",
          left: "-20%",
          width: "70%",
          height: "50%",
          background: "radial-gradient(ellipse, rgba(52,211,153,0.18) 0%, transparent 70%)",
          filter: "blur(40px)",
        }}
      />

      {/* Glow azul no rodapé */}
      <div
        className="absolute pointer-events-none"
        style={{
          bottom: "-10%",
          right: "-10%",
          width: "60%",
          height: "45%",
          background: "radial-gradient(ellipse, rgba(96,165,250,0.12) 0%, transparent 70%)",
          filter: "blur(50px)",
        }}
      />

      {/* Conteúdo */}
      <div
        className={sg.className}
        style={{
          position: "relative",
          zIndex: 10,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          padding: "3rem 3rem 2.5rem",
          gap: "2.5rem",
        }}
      >
        {/* Brand */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", marginBottom: "1.5rem" }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "10px",
                background: "linear-gradient(135deg, #34d399, #059669)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.1rem",
                boxShadow: "0 4px 16px rgba(52,211,153,0.35)",
              }}
            >
              🥗
            </div>
            <span
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                letterSpacing: "-0.03em",
                background: "linear-gradient(135deg, #6ee7b7, #34d399)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              CalorIA
            </span>
          </div>

          <h2
            style={{
              fontSize: "clamp(1.75rem, 2.8vw, 2.25rem)",
              fontWeight: 700,
              lineHeight: 1.2,
              letterSpacing: "-0.03em",
              color: "#f0fdf4",
              margin: 0,
            }}
          >
            Controle o que você come.{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #34d399 0%, #60a5fa 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Entenda seu corpo.
            </span>
          </h2>
          <p
            style={{
              marginTop: "0.75rem",
              fontSize: "0.9rem",
              color: "rgba(255,255,255,0.42)",
              lineHeight: 1.6,
              fontWeight: 400,
            }}
          >
            Diário alimentar inteligente com IA. Sem planilhas, sem complicação.
          </p>
        </div>

        {/* Feature cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem", flex: 1 }}>
          {FEATURES.map((f) => (
            <div
              key={f.icon}
              style={{
                display: "flex",
                gap: "1rem",
                padding: "1.125rem 1.25rem",
                borderRadius: "1rem",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderLeft: `3px solid ${f.accent}`,
                backdropFilter: "blur(12px)",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Glow sutil atrás do card */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: `radial-gradient(ellipse 60% 80% at 0% 50%, ${f.accent}0d 0%, transparent 70%)`,
                  pointerEvents: "none",
                }}
              />

              {/* Ícone */}
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: "0.75rem",
                  background: `linear-gradient(135deg, ${f.accent}20, ${f.accent}35)`,
                  border: `1px solid ${f.accent}40`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.35rem",
                  flexShrink: 0,
                  position: "relative",
                  zIndex: 1,
                }}
              >
                {f.icon}
              </div>

              {/* Texto */}
              <div style={{ position: "relative", zIndex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem", flexWrap: "wrap" }}>
                  <p
                    style={{
                      margin: 0,
                      fontSize: "0.8rem",
                      fontWeight: 700,
                      color: "rgba(255,255,255,0.9)",
                      lineHeight: 1.3,
                    }}
                  >
                    {f.headline}
                  </p>
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: "0.72rem",
                    color: "rgba(255,255,255,0.38)",
                    lineHeight: 1.55,
                  }}
                >
                  {f.body}
                </p>
                {/* Badge */}
                <span
                  style={{
                    display: "inline-block",
                    marginTop: "0.45rem",
                    fontSize: "0.65rem",
                    fontWeight: 600,
                    color: f.badgeColor,
                    background: `${f.badgeColor}18`,
                    border: `1px solid ${f.badgeColor}35`,
                    borderRadius: "99px",
                    padding: "0.15rem 0.6rem",
                    letterSpacing: "0.02em",
                  }}
                >
                  {f.badge}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Rodapé — social proof */}
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.07)",
            paddingTop: "1.25rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <p style={{ margin: 0, fontSize: "0.7rem", color: "rgba(255,255,255,0.2)" }}>
            CalorIA © {new Date().getFullYear()}
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 6px #34d399" }} />
            <span style={{ fontSize: "0.68rem", color: "rgba(255,255,255,0.3)" }}>Serviço online</span>
          </div>
        </div>
      </div>
    </div>
  );
}
