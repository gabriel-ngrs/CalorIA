import { ImageResponse } from "next/og";

// Recurso nativo do Next: nenhuma dependência nova foi adicionada para gerar a
// imagem, como o escopo travado da fase exige.
export const runtime = "edge";
export const alt = "CalorIA — Diário alimentar inteligente";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "80px",
          // Cores do design system atual: fundo escuro `--background` do dark
          // mode e verde `--primary`.
          background: "linear-gradient(135deg, #131929 0%, #1C2333 100%)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "20px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              width: "18px",
              height: "72px",
              borderRadius: "9px",
              background: "linear-gradient(180deg, #17C98A 0%, #F97316 100%)",
            }}
          />
          <div style={{ fontSize: 84, fontWeight: 700, color: "#E8ECF0" }}>
            CalorIA
          </div>
        </div>
        <div style={{ fontSize: 40, color: "#17C98A", marginBottom: "16px" }}>
          Diário alimentar inteligente
        </div>
        <div
          style={{
            fontSize: 30,
            color: "#94A3B8",
            maxWidth: "900px",
            lineHeight: 1.4,
          }}
        >
          Registre a refeição por texto ou foto. A IA analisa os macronutrientes,
          aprende seus hábitos e gera insights.
        </div>
      </div>
    ),
    size,
  );
}
