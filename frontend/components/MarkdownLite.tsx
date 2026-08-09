import React from "react";
import { cn } from "@/lib/utils";

/**
 * Renderizador de markdown mínimo, sem dependências (BUG 18).
 *
 * A IA retorna texto em markdown (**negrito**, títulos, listas). Antes o
 * frontend exibia o conteúdo cru, mostrando "**" e "**1)**" literais. Este
 * componente cobre o subconjunto que a IA de fato emite — negrito inline,
 * títulos (#) e itens de lista — sem trazer uma biblioteca de markdown.
 */

const BOLD_SPLIT = /(\*\*[^*]+\*\*)/g;
const BOLD_MATCH = /^\*\*([^*]+)\*\*$/;
const HEADING = /^#{1,6}\s+(.*)$/;
const BULLET = /^[-*]\s+(.*)$/;
const NUMBERED = /^(\d+[.)])\s+(.*)$/;

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  return text.split(BOLD_SPLIT).map((part, i) => {
    const bold = BOLD_MATCH.exec(part);
    const key = `${keyPrefix}-${i}`;
    if (bold) return <strong key={key}>{bold[1]}</strong>;
    return <React.Fragment key={key}>{part}</React.Fragment>;
  });
}

export function MarkdownLite({
  content,
  className,
}: {
  content: string;
  className?: string;
}) {
  const lines = content.split("\n");

  return (
    <div className={cn("text-sm leading-relaxed space-y-1", className)}>
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={i} className="h-2" aria-hidden />;

        const heading = HEADING.exec(trimmed);
        if (heading) {
          return (
            <p key={i} className="font-semibold">
              {renderInline(heading[1], `h-${i}`)}
            </p>
          );
        }

        const bullet = BULLET.exec(trimmed);
        if (bullet) {
          return (
            <div key={i} className="flex gap-2">
              <span aria-hidden>•</span>
              <span>{renderInline(bullet[1], `b-${i}`)}</span>
            </div>
          );
        }

        const numbered = NUMBERED.exec(trimmed);
        if (numbered) {
          return (
            <div key={i} className="flex gap-2">
              <span className="font-medium">{numbered[1]}</span>
              <span>{renderInline(numbered[2], `n-${i}`)}</span>
            </div>
          );
        }

        return <p key={i}>{renderInline(trimmed, `p-${i}`)}</p>;
      })}
    </div>
  );
}
