"use client";

import { Plasma } from "@/components/auth/Plasma";

const FEATURES = [
  {
    num: "01",
    accent: "#34d399",
    headline: "IA que entende o que você come",
    body: "Foto ou texto: Gemini 2.5 Flash identifica calorias, proteínas e carbs em segundos.",
    badge: "Gemini 2.5 Flash",
  },
  {
    num: "02",
    accent: "#6ee7b7",
    headline: "20 mil+ alimentos catalogados",
    body: "TACO + Open Food Facts. Arroz com feijão, frango grelhado, qualquer prato brasileiro.",
    badge: "Banco nacional",
  },
  {
    num: "03",
    accent: "#60a5fa",
    headline: "Veja sua evolução completa",
    body: "Peso, hidratação e humor num só lugar. Entenda como sua dieta afeta como você se sente.",
    badge: "Insights diários",
  },
  {
    num: "04",
    accent: "#a78bfa",
    headline: "Metas calculadas para você",
    body: "TDEE personalizado com altura, peso, idade e objetivo. Calorias e macros no seu ritmo.",
    badge: "100% personalizado",
  },
  {
    num: "05",
    accent: "#fb923c",
    headline: "Lembretes sem abrir o app",
    body: "Notificações Web Push nativas no celular ou desktop. Você registra, a IA cuida do resto.",
    badge: "Web Push nativo",
  },
];

export function AuthLeftPanel() {
  return (
    <div
      className="hidden lg:flex relative flex-col overflow-hidden"
      style={{ width: "46%", minHeight: "100vh" }}
    >
      {/* Fundo — sempre escuro, independente do tema */}
      <div
        className="absolute inset-0"
        style={{ background: "linear-gradient(160deg, #071f12 0%, #0b1e30 52%, #060e1a 100%)" }}
      />

      {/* Plasma */}
      <div className="absolute inset-0" style={{ opacity: 0.2 }}>
        <Plasma speed={0.2} scale={1.3} opacity={0.85} />
      </div>

      {/* Glow verde topo-esquerda */}
      <div className="absolute pointer-events-none" style={{
        top: "-8%", left: "-10%", width: "60%", height: "50%",
        background: "radial-gradient(ellipse, rgba(52,211,153,0.18) 0%, transparent 68%)",
        filter: "blur(48px)",
      }} />

      {/* Glow azul rodapé */}
      <div className="absolute pointer-events-none" style={{
        bottom: "-8%", right: "-8%", width: "55%", height: "45%",
        background: "radial-gradient(ellipse, rgba(96,165,250,0.12) 0%, transparent 68%)",
        filter: "blur(56px)",
      }} />

      {/* Conteúdo */}
      <div
        style={{
          position: "relative",
          zIndex: 10,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          padding: "3rem 2.75rem 2.5rem",
          gap: "0",
        }}
      >
        {/* ── Brand ── */}
        <div style={{ marginBottom: "2rem" }}>
          {/* Nome em destaque — cor sólida, sem clip */}
          <h1
            style={{
              fontSize: "clamp(3.2rem, 5vw, 4.5rem)",
              fontWeight: 700,
              lineHeight: 1,
              letterSpacing: "-0.045em",
              margin: 0,
              color: "#34d399",
              textShadow: "0 0 40px rgba(52,211,153,0.35)",
            }}
          >
            CalorIA
          </h1>

          <p style={{
            marginTop: "0.55rem",
            fontSize: "0.88rem",
            fontWeight: 400,
            color: "rgba(255,255,255,0.45)",
            letterSpacing: "0.01em",
          }}>
            Seu diário alimentar,{" "}
            <span style={{ fontWeight: 600, color: "#6ee7b7" }}>do jeito certo</span>
          </p>

          {/* Headline de impacto */}
          <h2 style={{
            marginTop: "1.75rem",
            fontSize: "clamp(1.2rem, 2vw, 1.5rem)",
            fontWeight: 700,
            lineHeight: 1.3,
            letterSpacing: "-0.025em",
            color: "#f0fdf4",
            margin: "1.75rem 0 0",
          }}>
            Controle o que você come.{" "}
            <span style={{ color: "#34d399" }}>Entenda seu corpo.</span>
          </h2>
        </div>

        {/* ── Feature cards ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", flex: 1 }}>
          {FEATURES.map((f) => (
            <div
              key={f.badge}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "1rem",
                padding: "1rem 1.125rem",
                borderRadius: "0.875rem",
                background: "rgba(255,255,255,0.055)",
                border: "1px solid rgba(255,255,255,0.10)",
                borderLeft: `3px solid ${f.accent}`,
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* glow atrás */}
              <div style={{
                position: "absolute", inset: 0, pointerEvents: "none",
                background: `radial-gradient(ellipse 60% 100% at 0% 50%, ${f.accent}12 0%, transparent 70%)`,
              }} />

              {/* número */}
              <div style={{
                width: 36, height: 36, borderRadius: "0.5rem", flexShrink: 0,
                background: `${f.accent}22`,
                border: `1px solid ${f.accent}45`,
                display: "flex", alignItems: "center", justifyContent: "center",
                position: "relative", zIndex: 1,
              }}>
                <span style={{
                  fontSize: "0.7rem", fontWeight: 700,
                  color: f.accent, letterSpacing: "0.02em",
                }}>
                  {f.num}
                </span>
              </div>

              {/* texto */}
              <div style={{ position: "relative", zIndex: 1, minWidth: 0 }}>
                <p style={{
                  margin: 0,
                  fontSize: "0.875rem",
                  fontWeight: 700,
                  color: "#ffffff",
                  lineHeight: 1.3,
                }}>
                  {f.headline}
                </p>
                <p style={{
                  margin: "0.3rem 0 0.45rem",
                  fontSize: "0.775rem",
                  color: "rgba(255,255,255,0.62)",
                  lineHeight: 1.6,
                }}>
                  {f.body}
                </p>
                <span style={{
                  display: "inline-block",
                  fontSize: "0.65rem", fontWeight: 600,
                  color: f.accent,
                  background: `${f.accent}18`,
                  border: `1px solid ${f.accent}38`,
                  borderRadius: "99px",
                  padding: "0.15rem 0.6rem",
                  letterSpacing: "0.03em",
                }}>
                  {f.badge}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Rodapé ── */}
        <div style={{
          borderTop: "1px solid rgba(255,255,255,0.07)",
          marginTop: "1.5rem",
          paddingTop: "1rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <p style={{ margin: 0, fontSize: "0.65rem", color: "rgba(255,255,255,0.18)" }}>
            CalorIA © {new Date().getFullYear()}
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <div style={{
              width: 6, height: 6, borderRadius: "50%",
              background: "#34d399", boxShadow: "0 0 8px #34d399aa",
            }} />
            <span style={{ fontSize: "0.63rem", color: "rgba(255,255,255,0.25)" }}>
              Serviço online
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
