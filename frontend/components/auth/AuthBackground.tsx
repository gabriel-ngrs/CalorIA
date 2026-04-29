"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/* ─── Orbes de fundo ─────────────────────────────────────── */
const ORBS = [
  { color: "#10B981", size: 340, top: "-10%", left: "auto", right: "2%",   bottom: "auto",  blur: 64, opacity: 0.28, duration: 6,   delay: 0   },
  { color: "#60A5FA", size: 400, top: "auto", left: "0%",   right: "auto", bottom: "-12%",  blur: 72, opacity: 0.24, duration: 7.5, delay: 2   },
  { color: "#F97316", size: 220, top: "40%",  left: "0%",   right: "auto", bottom: "auto",  blur: 52, opacity: 0.24, duration: 5.5, delay: 1   },
  { color: "#EAB308", size: 160, top: "10%",  left: "auto", right: "16%",  bottom: "auto",  blur: 44, opacity: 0.18, duration: 8,   delay: 3   },
  { color: "#22C55E", size: 240, top: "auto", left: "auto", right: "4%",   bottom: "20%",   blur: 52, opacity: 0.18, duration: 6.5, delay: 1.5 },
  { color: "#8B5CF6", size: 140, top: "53%",  left: "auto", right: "28%",  bottom: "auto",  blur: 40, opacity: 0.14, duration: 9,   delay: 4   },
];

/* ─── Fotos de comida ────────────────────────────────────── */
const FOODS = [
  { src: "/food/avocado.jpg",  size: 96,  top: "8%",   left: "23%", delay: 0.5, dur: 5.2 },
  { src: "/food/apple.jpg",    size: 78,  top: "16%",  left: "60%", delay: 1.8, dur: 6.1 },
  { src: "/food/broccoli.jpg", size: 108, top: "72%",  left: "18%", delay: 0.9, dur: 7.0 },
  { src: "/food/orange.jpg",   size: 84,  top: "78%",  left: "62%", delay: 2.8, dur: 5.6 },
  { src: "/food/berries.jpg",  size: 72,  top: "44%",  left: "82%", delay: 1.3, dur: 6.8 },
  { src: "/food/carrot.jpg",   size: 88,  top: "55%",  left: "36%", delay: 3.1, dur: 5.0 },
  { src: "/food/salad.jpg",    size: 100, top: "28%",  left: "13%", delay: 0.7, dur: 7.3 },
  { src: "/food/salmon.jpg",   size: 80,  top: "20%",  left: "75%", delay: 2.4, dur: 6.4 },
  { src: "/food/banana.jpg",   size: 76,  top: "86%",  left: "43%", delay: 1.6, dur: 5.8 },
  { src: "/food/egg.jpg",      size: 68,  top: "5%",   left: "46%", delay: 3.5, dur: 6.0 },
];

/* ─── Cards de features — posições livres ─────────────────── */
const FEATURES = [
  { id: "ai",      icon: "🤖", label: "IA analisa macros",      sub: "Gemini 2.5 Flash",      color: "#10B981", homeX: 2,  homeY: 12, floatDelay: 0.0, floatDur: 5.0 },
  { id: "history", icon: "📊", label: "Histórico detalhado",    sub: "Gráficos e tendências",  color: "#60A5FA", homeX: 2,  homeY: 44, floatDelay: 1.4, floatDur: 6.2 },
  { id: "water",   icon: "💧", label: "Hidratação diária",      sub: "Metas personalizadas",   color: "#3B82F6", homeX: 3,  homeY: 74, floatDelay: 0.7, floatDur: 5.8 },
  { id: "weight",  icon: "⚖️", label: "Evolução de peso",       sub: "Linha do tempo visual",  color: "#22C55E", homeX: 76, homeY: 14, floatDelay: 0.4, floatDur: 6.5 },
  { id: "mood",    icon: "😊", label: "Humor e energia",        sub: "Correlação com dieta",   color: "#8B5CF6", homeX: 77, homeY: 48, floatDelay: 2.1, floatDur: 5.4 },
  { id: "remind",  icon: "🔔", label: "Lembretes inteligentes", sub: "Web Push nativo",        color: "#F97316", homeX: 74, homeY: 76, floatDelay: 1.1, floatDur: 7.0 },
];

/* ─── Card magnético ─────────────────────────────────────── */
function MagneticCard({
  feat, mousePx, mounted, index,
}: {
  feat: (typeof FEATURES)[number];
  mousePx: { x: number; y: number };
  mounted: boolean;
  index: number;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [magnet, setMagnet]   = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);
  const [tilt, setTilt]       = useState({ rx: 0, ry: 0 });

  useEffect(() => {
    if (!mounted || hovered) {
      setMagnet({ x: 0, y: 0 });
      return;
    }
    // usa a posição HOME (percentual × viewport) como referência fixa
    // assim o card em movimento não cria loop de feedback
    const cx = (feat.homeX / 100) * window.innerWidth  + 105; // 105 ≈ metade da largura do card
    const cy = (feat.homeY / 100) * window.innerHeight +  35; // 35  ≈ metade da altura do card
    const dx = mousePx.x - cx;
    const dy = mousePx.y - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const RADIUS   = 240;
    const MAX_PULL = 36;
    if (dist < RADIUS && dist > 0) {
      const strength = ((RADIUS - dist) / RADIUS) * MAX_PULL;
      setMagnet({ x: (dx / dist) * strength, y: (dy / dist) * strength });
    } else {
      setMagnet({ x: 0, y: 0 });
    }
  }, [mousePx, mounted, hovered, feat.homeX, feat.homeY]);

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setTilt({
      rx: ((e.clientY - rect.top  - rect.height / 2) / (rect.height / 2)) * -12,
      ry: ((e.clientX - rect.left - rect.width  / 2) / (rect.width  / 2)) *  12,
    });
  };

  const fromRight    = feat.homeX > 50;
  const enterOffset  = mounted ? 0 : (fromRight ? 80 : -80);

  return (
    <div
      className="absolute hidden xl:block"
      style={{
        left:      `${feat.homeX}%`,
        top:       `${feat.homeY}%`,
        opacity:   mounted ? 1 : 0,
        transform: `translate(${magnet.x + enterOffset}px, ${magnet.y}px)`,
        transition:`opacity 0.55s ease ${index * 0.13}s, transform 0.4s cubic-bezier(0.23,1,0.32,1)`,
        zIndex:    hovered ? 20 : 10,
      }}
    >
      {/* float independente — amplitude maior */}
      <div style={{ animation: `floatCard ${feat.floatDur}s ease-in-out ${feat.floatDelay}s infinite` }}>
        <div
          ref={cardRef}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => { setHovered(false); setTilt({ rx: 0, ry: 0 }); }}
          onMouseMove={onMouseMove}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "12px 16px 12px 12px",
            minWidth: 210,
            borderRadius: 20,
            cursor: "default",
            userSelect: "none",
            background: hovered
              ? `linear-gradient(135deg, rgba(255,255,255,0.98) 50%, ${feat.color}22)`
              : "rgba(255,255,255,0.82)",
            backdropFilter: "blur(18px)",
            WebkitBackdropFilter: "blur(18px)",
            border: `1.5px solid ${hovered ? feat.color + "88" : "rgba(255,255,255,0.95)"}`,
            boxShadow: hovered
              ? `0 20px 60px ${feat.color}40, 0 4px 16px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,1)`
              : `0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.95)`,
            transform: `perspective(700px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg) scale(${hovered ? 1.08 : 1})`,
            transition: "transform 0.2s ease, box-shadow 0.3s ease, background 0.3s ease, border-color 0.3s ease",
          }}
        >
          {/* ícone */}
          <div style={{
            width: 46, height: 46, borderRadius: 14, flexShrink: 0,
            background: `linear-gradient(135deg, ${feat.color}30, ${feat.color}60)`,
            border: `1.5px solid ${feat.color}55`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1.4rem",
            boxShadow: `0 4px 12px ${feat.color}30`,
            transform: hovered ? "scale(1.2) rotate(-6deg)" : "scale(1) rotate(0deg)",
            transition: "transform 0.25s cubic-bezier(0.34,1.56,0.64,1)",
          }}>
            {feat.icon}
          </div>

          {/* texto */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f172a", lineHeight: 1.2, margin: 0, whiteSpace: "nowrap" }}>
              {feat.label}
            </p>
            <p style={{ fontSize: "0.65rem", color: "#64748b", lineHeight: 1.4, margin: "3px 0 0", whiteSpace: "nowrap" }}>
              {feat.sub}
            </p>
          </div>

          {/* dot pulsando */}
          <div style={{ position: "relative", width: 9, height: 9, flexShrink: 0 }}>
            <div style={{
              position: "absolute", inset: 0, borderRadius: "50%",
              backgroundColor: feat.color, opacity: 0.35,
              animation: "ping 1.8s cubic-bezier(0,0,0.2,1) infinite",
            }} />
            <div style={{ position: "absolute", inset: "1px", borderRadius: "50%", backgroundColor: feat.color }} />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Componente principal ───────────────────────────────── */
export function AuthBackground() {
  const [mouse,   setMouse]   = useState({ x: 0, y: 0 });
  const [mousePx, setMousePx] = useState({ x: -999, y: -999 });
  const [mounted, setMounted] = useState(false);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    setMouse({
      x: (e.clientX / window.innerWidth  - 0.5) * 2,
      y: (e.clientY / window.innerHeight - 0.5) * 2,
    });
    setMousePx({ x: e.clientX, y: e.clientY });
  }, []);

  useEffect(() => {
    setMounted(true);
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [handleMouseMove]);

  const tx = (d: number) => `${mouse.x * d * 100}px`;
  const ty = (d: number) => `${mouse.y * d * 100}px`;

  return (
    <>
      {/* spotlight cursor */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: `radial-gradient(600px circle at ${mousePx.x}px ${mousePx.y}px, rgba(16,185,129,0.07) 0%, transparent 65%)`,
      }} />

      {/* gradiente base */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: `
          radial-gradient(ellipse 70% 55% at 100% 0%, rgba(16,185,129,0.13) 0%, transparent 60%),
          radial-gradient(ellipse 60% 50% at 0% 100%, rgba(96,165,250,0.11) 0%, transparent 55%),
          radial-gradient(ellipse 45% 40% at 50% 110%, rgba(249,115,22,0.06) 0%, transparent 50%)
        `,
      }} />

      {/* orbes */}
      {ORBS.map((orb, i) => (
        <div key={i} className="absolute pointer-events-none" style={{
          top: orb.top, left: orb.left, right: orb.right, bottom: orb.bottom,
          transform: mounted ? `translate(${tx(0.018)}, ${ty(0.018)})` : "translate(0,0)",
          transition: "transform 0.18s ease-out",
        }}>
          <div style={{
            width: orb.size, height: orb.size, borderRadius: "50%",
            background: `radial-gradient(circle, ${orb.color} 0%, transparent 70%)`,
            filter: `blur(${orb.blur}px)`, opacity: orb.opacity,
            animation: `float ${orb.duration}s ease-in-out ${orb.delay}s infinite`,
          }} />
        </div>
      ))}

      {/* fotos de comida — ocultas em mobile */}
      {FOODS.map((f, i) => {
        const depth = 0.03 + (i * 0.005) % 0.025;
        return (
          <div key={i} className="absolute pointer-events-none select-none hidden lg:block" style={{
            top: f.top, left: f.left,
            transform: mounted ? `translate(${tx(depth)}, ${ty(depth)})` : "translate(0,0)",
            transition: "transform 0.14s ease-out",
          }}>
            <div style={{ animation: `float ${f.dur}s ease-in-out ${f.delay}s infinite` }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={f.src}
                alt=""
                width={f.size}
                height={f.size}
                style={{
                  width: f.size, height: f.size,
                  borderRadius: "50%",
                  objectFit: "cover",
                  opacity: 0.88,
                  display: "block",
                  boxShadow: "0 8px 28px rgba(0,0,0,0.18), 0 0 0 4px rgba(255,255,255,0.85)",
                  filter: "saturate(1.2) brightness(1.03)",
                }}
              />
            </div>
          </div>
        );
      })}

      {/* cards magnéticos */}
      {FEATURES.map((feat, i) => (
        <MagneticCard key={feat.id} feat={feat} mousePx={mousePx} mounted={mounted} index={i} />
      ))}


      <style>{`
        @keyframes floatCard {
          0%   { transform: translateY(0px) rotate(0deg); }
          30%  { transform: translateY(-14px) rotate(0.4deg); }
          60%  { transform: translateY(-8px) rotate(-0.3deg); }
          100% { transform: translateY(0px) rotate(0deg); }
        }
        @keyframes ping {
          75%, 100% { transform: scale(2.4); opacity: 0; }
        }
      `}</style>
    </>
  );
}
