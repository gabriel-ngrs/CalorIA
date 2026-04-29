"use client";

import { Space_Grotesk } from "next/font/google";
import { Plasma } from "@/components/auth/Plasma";
import { useTheme } from "@/components/theme-provider";

const sg = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const FEATURES = [
  {
    icon: "🤖",
    accent: "#10b981",
    headline: "IA que entende o que você come",
    body: "Descreva em texto ou mande uma foto. Gemini 2.5 Flash identifica calorias, proteínas e carbs na hora.",
    badge: "Gemini 2.5 Flash",
  },
  {
    icon: "🍽️",
    accent: "#34d399",
    headline: "20 mil+ alimentos catalogados",
    body: "Base TACO + Open Food Facts. Encontra arroz com feijão, frango grelhado ou qualquer prato brasileiro.",
    badge: "Banco nacional",
  },
  {
    icon: "📊",
    accent: "#60a5fa",
    headline: "Veja sua evolução completa",
    body: "Gráficos de peso, hidratação e humor em uma tela só. Descubra como sua dieta afeta como você se sente.",
    badge: "Insights diários",
  },
  {
    icon: "🎯",
    accent: "#a78bfa",
    headline: "Metas calculadas para você",
    body: "TDEE personalizado com base na sua altura, peso, idade e objetivo. Calorias e macros no seu ritmo.",
    badge: "100% personalizado",
  },
  {
    icon: "🔔",
    accent: "#fb923c",
    headline: "Lembretes sem abrir o app",
    body: "Notificações Web Push nativas no seu celular ou desktop. Você registra, a IA cuida do resto.",
    badge: "Web Push nativo",
  },
];

export function AuthLeftPanel() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const bg = isDark
    ? "linear-gradient(160deg, #061a10 0%, #0a1628 55%, #050e18 100%)"
    : "linear-gradient(160deg, #f0fdf4 0%, #eff6ff 55%, #f8fafc 100%)";

  const headingColor   = isDark ? "#f0fdf4"              : "#0f1f0f";
  const bodyColor      = isDark ? "rgba(255,255,255,0.38)" : "rgba(0,0,0,0.42)";
  const cardBg         = isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.75)";
  const cardBorder     = isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.08)";
  const taglineColor   = isDark ? "rgba(255,255,255,0.4)"  : "rgba(0,0,0,0.4)";
  const footerColor    = isDark ? "rgba(255,255,255,0.18)" : "rgba(0,0,0,0.2)";
  const dotColor       = isDark ? "rgba(52,211,153,0.5)"   : "#10b981";
  const dotLabel       = isDark ? "rgba(255,255,255,0.28)" : "rgba(0,0,0,0.3)";
  const sepColor       = isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.07)";
  const badgeBg = (accent: string) => isDark ? `${accent}18` : `${accent}15`;
  const badgeBorder = (accent: string) => isDark ? `${accent}35` : `${accent}40`;

  return (
    <div
      className="hidden lg:flex relative flex-col overflow-hidden overflow-y-auto"
      style={{ width: "48%", minHeight: "100vh" }}
    >
      {/* Fundo */}
      <div className="absolute inset-0" style={{ background: bg }} />

      {/* Plasma — só no dark */}
      {isDark && (
        <div className="absolute inset-0" style={{ opacity: 0.22 }}>
          <Plasma speed={0.2} scale={1.3} opacity={0.8} />
        </div>
      )}

      {/* Glows */}
      <div className="absolute pointer-events-none" style={{
        top: "-5%", left: "-15%", width: "65%", height: "45%",
        background: isDark
          ? "radial-gradient(ellipse, rgba(52,211,153,0.15) 0%, transparent 70%)"
          : "radial-gradient(ellipse, rgba(16,185,129,0.12) 0%, transparent 70%)",
        filter: "blur(40px)",
      }} />
      <div className="absolute pointer-events-none" style={{
        bottom: "-8%", right: "-8%", width: "55%", height: "40%",
        background: isDark
          ? "radial-gradient(ellipse, rgba(96,165,250,0.1) 0%, transparent 70%)"
          : "radial-gradient(ellipse, rgba(96,165,250,0.08) 0%, transparent 70%)",
        filter: "blur(50px)",
      }} />

      {/* Conteúdo */}
      <div
        className={sg.className}
        style={{
          position: "relative",
          zIndex: 10,
          display: "flex",
          flexDirection: "column",
          minHeight: "100vh",
          padding: "3rem 3rem 2.5rem",
          gap: "2rem",
        }}
      >
        {/* ── CalorIA em evidência ── */}
        <div>
          <h1
            style={{
              fontSize: "clamp(3.5rem, 5.5vw, 5rem)",
              fontWeight: 700,
              lineHeight: 1,
              letterSpacing: "-0.045em",
              margin: 0,
              background: isDark
                ? "linear-gradient(135deg, #6ee7b7 0%, #34d399 45%, #60a5fa 100%)"
                : "linear-gradient(135deg, #059669 0%, #10b981 50%, #3b82f6 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            CalorIA
          </h1>
          <p style={{
            marginTop: "0.6rem",
            fontSize: "0.95rem",
            fontWeight: 400,
            color: taglineColor,
            letterSpacing: "0.01em",
          }}>
            Seu diário alimentar,{" "}
            <span style={{
              fontWeight: 600,
              color: isDark ? "#34d399" : "#059669",
            }}>
              do jeito certo
            </span>
          </p>

          {/* Headline de impacto */}
          <h2
            style={{
              marginTop: "1.75rem",
              fontSize: "clamp(1.25rem, 2.2vw, 1.6rem)",
              fontWeight: 700,
              lineHeight: 1.25,
              letterSpacing: "-0.025em",
              color: headingColor,
            }}
          >
            Controle o que você come.{" "}
            <span style={{
              background: isDark
                ? "linear-gradient(135deg, #34d399, #60a5fa)"
                : "linear-gradient(135deg, #059669, #3b82f6)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}>
              Entenda seu corpo.
            </span>
          </h2>
        </div>

        {/* ── Cards de feature ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", flex: 1 }}>
          {FEATURES.map((f) => (
            <div
              key={f.icon}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "1rem",
                padding: "1rem 1.125rem",
                borderRadius: "0.875rem",
                background: cardBg,
                border: `1px solid ${cardBorder}`,
                borderLeft: `3px solid ${f.accent}`,
                backdropFilter: "blur(10px)",
                WebkitBackdropFilter: "blur(10px)",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Glow atrás do card */}
              <div style={{
                position: "absolute", inset: 0, pointerEvents: "none",
                background: `radial-gradient(ellipse 50% 100% at 0% 50%, ${f.accent}${isDark ? "0c" : "09"} 0%, transparent 70%)`,
              }} />

              {/* Ícone */}
              <div style={{
                width: 40, height: 40, borderRadius: "0.625rem", flexShrink: 0,
                background: `${f.accent}${isDark ? "22" : "18"}`,
                border: `1px solid ${f.accent}${isDark ? "40" : "35"}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "1.2rem",
                position: "relative", zIndex: 1,
              }}>
                {f.icon}
              </div>

              {/* Texto */}
              <div style={{ position: "relative", zIndex: 1, minWidth: 0 }}>
                <p style={{
                  margin: 0, fontSize: "0.78rem", fontWeight: 700,
                  color: headingColor, lineHeight: 1.3,
                }}>
                  {f.headline}
                </p>
                <p style={{
                  margin: "0.25rem 0 0.4rem", fontSize: "0.7rem",
                  color: bodyColor, lineHeight: 1.55,
                }}>
                  {f.body}
                </p>
                <span style={{
                  display: "inline-block",
                  fontSize: "0.62rem", fontWeight: 600,
                  color: f.accent,
                  background: badgeBg(f.accent),
                  border: `1px solid ${badgeBorder(f.accent)}`,
                  borderRadius: "99px",
                  padding: "0.12rem 0.55rem",
                  letterSpacing: "0.02em",
                }}>
                  {f.badge}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Rodapé ── */}
        <div style={{
          borderTop: `1px solid ${sepColor}`,
          paddingTop: "1rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <p style={{ margin: 0, fontSize: "0.68rem", color: footerColor }}>
            CalorIA © {new Date().getFullYear()}
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <div style={{
              width: 6, height: 6, borderRadius: "50%",
              background: dotColor,
              boxShadow: `0 0 6px ${dotColor}`,
            }} />
            <span style={{ fontSize: "0.65rem", color: dotLabel }}>Serviço online</span>
          </div>
        </div>
      </div>
    </div>
  );
}
