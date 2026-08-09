"use client";

import { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "light",
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    // O script inline de `layout.tsx` já aplicou a classe antes do paint. Aqui
    // o estado só se alinha ao que está no DOM — nada é reaplicado, para não
    // reintroduzir o flash que o script eliminou.
    const stored = localStorage.getItem("caloria-theme") as Theme | null;
    setTheme(
      stored ??
        (document.documentElement.classList.contains("dark") ? "dark" : "light"),
    );
  }, []);

  const toggleTheme = () => {
    const next: Theme = theme === "light" ? "dark" : "light";
    setTheme(next);
    localStorage.setItem("caloria-theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
