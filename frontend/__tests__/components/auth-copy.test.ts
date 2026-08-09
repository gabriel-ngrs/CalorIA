import { readFileSync } from "fs";
import { join } from "path";

const AUTH_COMPONENTS = [
  "components/auth/AuthLeftPanel.tsx",
  "components/auth/AuthBackground.tsx",
];

describe("Copy de auth alinhada ao provedor real (AC-D4, ADR-002)", () => {
  it.each(AUTH_COMPONENTS)(
    "%s não menciona mais 'Gemini' e cita Groq/Llama",
    (relativePath) => {
      const source = readFileSync(join(process.cwd(), relativePath), "utf-8");
      expect(source).not.toMatch(/Gemini/i);
      expect(source).toMatch(/Groq/i);
    },
  );
});
