import { Space_Grotesk } from "next/font/google";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export function AuthBrand() {
  return (
    <div className="text-center select-none" style={{ marginBottom: "1.75rem" }}>
      {/* Wrapper recebe o drop-shadow — separado do clip de gradiente */}
      <div style={{ filter: "drop-shadow(0 4px 16px rgba(6,95,70,0.18))" }}>
        <h1
          className={spaceGrotesk.className}
          style={{
            fontSize: "clamp(2.4rem, 10vw, 4.5rem)",
            fontWeight: 700,
            lineHeight: 1,
            margin: 0,
            letterSpacing: "-0.04em",
            background: "linear-gradient(135deg, #064e3b 0%, #065f46 40%, #0e7490 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          CalorIA
        </h1>
      </div>

      {/* Divisor */}
      <div style={{
        width: 32,
        height: 2,
        margin: "12px auto 14px",
        borderRadius: 99,
        background: "linear-gradient(90deg, transparent, #065f46, transparent)",
        opacity: 0.4,
      }} />

      {/* Slogan */}
      <p
        className={spaceGrotesk.className}
        style={{
          fontSize: "clamp(0.82rem, 3.5vw, 0.95rem)",
          fontWeight: 400,
          fontStyle: "normal",
          color: "#475569",
          margin: 0,
          letterSpacing: "0.01em",
        }}
      >
        Seu diário alimentar,{" "}
        <span style={{ fontWeight: 600, color: "#065f46" }}>do jeito certo</span>
      </p>
    </div>
  );
}
