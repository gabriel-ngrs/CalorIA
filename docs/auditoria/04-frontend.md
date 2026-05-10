# Frente D — Frontend

**Plano:** ver `plano.md` § Frente D.

## Achados desta frente

- AUD-018 (🟡 média) — Páginas e componentes inflados: `refeicoes/page.tsx` 1055 LOC, `QuickAddModals.tsx` 657, `insights/page.tsx` 611, `relatorios/page.tsx` 548

## D.1 Páginas e componentes grandes

Comando: `wc -l frontend/app/(dashboard)/*/page.tsx frontend/components/dashboard/*.tsx | sort -rn`. Artefato: `artefatos/D1-paginas-loc.txt`.

| Arquivo | LOC | Avaliação |
|---|---|---|
| `app/(dashboard)/refeicoes/page.tsx` | **1055** | 🔴 god component — > 1000 LOC, mistura listagem, criação por texto, foto, edição, exclusão |
| `components/dashboard/QuickAddModals.tsx` | 657 | 🟠 múltiplos modais num único arquivo |
| `app/(dashboard)/insights/page.tsx` | 611 | 🟠 painel agregando múltiplas seções |
| `app/(dashboard)/relatorios/page.tsx` | 548 | 🟠 |
| `app/(dashboard)/lembretes/page.tsx` | 484 | 🟡 |
| `app/(dashboard)/dashboard/page.tsx` | 413 | 🟡 |
| `app/(dashboard)/perfil/page.tsx` | 366 | 🟡 |
| `app/(dashboard)/humor/page.tsx` | 337 | 🟡 |
| `app/(dashboard)/hidratacao/page.tsx` | 282 | OK |
| `app/(dashboard)/peso/page.tsx` | 278 | OK |
| `components/dashboard/MacroPieChart.tsx` | 132 | OK |
| `components/dashboard/MacroCards.tsx` | 131 | OK |

**Hotspot**: `refeicoes/page.tsx` (1055 LOC). 25 ícones importados, mistura UI declarativa + lógica de mic/voice + foto + form. Plano de quebra:

```
refeicoes/
├── page.tsx                      # composição + estado top-level (≤200)
├── _components/
│   ├── MealList.tsx              # listagem + paginação
│   ├── MealItemCard.tsx          # card individual editável
│   ├── AddMealTextDialog.tsx     # criação por texto + voz
│   ├── AddMealPhotoDialog.tsx    # criação por foto
│   └── EditMealItemDialog.tsx
└── _hooks/
    └── useVoiceCapture.ts        # logic mic/SpeechRecognition
```

`QuickAddModals.tsx` segue padrão similar — quebrar em 1 arquivo por modal.

Achado: AUD-018 (🟡) cobrindo todos os arquivos > 500 LOC.

## Notas e contexto

(texto livre conforme aprendizagens surgem)
