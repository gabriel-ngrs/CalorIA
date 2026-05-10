# Frente D — Frontend

**Plano:** ver `plano.md` § Frente D.

## Achados desta frente

- AUD-018 (🟡 média) — Páginas e componentes inflados: `refeicoes/page.tsx` 1055 LOC, `QuickAddModals.tsx` 657, `insights/page.tsx` 611, `relatorios/page.tsx` 548
- AUD-019 (🟢 baixa) — Hooks de mutação não usam optimistic updates onde caberia (toggle reminder, mark notification read, etc.)
- AUD-020 (🟢 baixa) — 7 sites `console.log/error` em `api.ts`+`providers.tsx` rodam em produção (sem gate `NODE_ENV`)
- AUD-021 (🟠 alta) — Discrepância de contrato `/auth/login`: backend retorna `{access_token, refresh_token}` mas frontend lê `data.user.id`/`data.user.name` (silently degraded)
- AUD-022 (🟢 baixa) — 6 `any` para Web Speech API (SpeechRecognition) duplicados entre 2 arquivos
- AUD-023 (🟢 baixa) — Service Worker sem `skipWaiting`/`clients.claim`; manifest sem `apple-touch-icon` e ícones para todos os tamanhos requisitados pelo Lighthouse PWA

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

## D.2 Hooks customizados (TanStack Query)

Inspeção: `frontend/lib/hooks/*.ts` (8 arquivos, 622 LOC) + `frontend/app/providers.tsx`.

**Defaults globais (em `providers.tsx:43-65`)** ✅ bem ajustados:
- `staleTime: 3 * 60_000` (3 min — não refetch ao navegar)
- `gcTime: 10 * 60_000` (10 min)
- `refetchOnWindowFocus: false`
- `retry`: skip 401 (delegado ao interceptor axios), 1 retry para outros

**Cobertura por hook**

| Hook | useQuery | useMutation | Invalida em onSuccess | Optimistic |
|---|---|---|---|---|
| `useDashboard` | ✅ | — | — | — |
| `useMeals` | ✅ | ✅ | ✅ (`meals`, `dashboard`) | ❌ |
| `useLogs` (Weight/Hydration/Mood) | ✅ | ✅ | ✅ | ❌ |
| `useReminders` | ✅ | ✅ | ✅ (`reminders`) | ❌ |
| `useNotifications` | ✅ | ✅ | ✅ (`notifications`) | ❌ |
| `useProfile` | ✅ (staleTime 15min override) | ✅ | ✅ | ❌ |
| `useAI` | — | ✅ | — (sem cache invalidation; AI é mutation pura) | — |
| `usePushNotifications` | — (vanilla `useState`+`useEffect`) | — | — | — |

**Padrões corretos:**
- queryKey explícito em todas
- `useQueryClient()` para invalidações pontuais (`useReminders`, `useLogs`, `useMeals`, `useProfile`)
- `staleTime` override quando faz sentido (notifications 15s, profile 15min)

**Oportunidades:**
- **Optimistic updates ausentes em todos os hooks de mutação** — `toggleReminder`, `markNotificationRead`, `markAllRead`, `deleteMealItem` são candidatos perfeitos (operações idempotentes/reversíveis). UX percebida fica melhor sem latência aparente.
- `QueryCache` configura `onSuccess` e `onError` com `console.log` — **roda em produção**. Será cobrado em D.3 (PASSO 5.3).

Achado registrado: AUD-019 (🟢) — oportunidade de optimistic updates.

## D.3 Camada API (`frontend/lib/api.ts`)

Arquivo: `frontend/lib/api.ts` (122 linhas).

**Fluxo de token** ✅ bem desenhado:

| Mecanismo | Detalhe |
|---|---|
| Cache em memória | 90s (`PROACTIVE_REFRESH_BUFFER_MS = 2 * 60_000`) |
| Promise dedupe | `_pendingSession` evita N×`getSession()` simultâneos |
| Refresh proativo | Se token expira em < 2 min, ignora cache |
| 401 retry transparente | Flag `_retry` evita loop; invalida cache + busca fresco + reenvia |
| Falha de refresh | `RefreshAccessTokenError` → `signOut({ redirect: true })` |
| Timeout request | 45s (alto, mas justifica análises de IA longas) |
| Sync com sessão | `setApiToken(...)` chamado pelo `SessionSync` em `providers.tsx` quando sessão muda — **sem HTTP extra** |

**Logs em produção** ⚠️

Apenas o `ReactQueryDevtools` está protegido por `process.env.NODE_ENV === "development"` (`providers.tsx:77`). Tudo abaixo roda em produção:

| Local | Linha | Volume típico | Sensibilidade |
|---|---|---|---|
| `api.ts:63` | `[API→] GET /...  (auth: Xms via cache)` | 1 por request | URL só |
| `api.ts:88` | `[API←] GET /...  200  Xms` | 1 por response OK | URL + status |
| `api.ts:97` | `[API✗] GET /...  ERR  Xms — message` | 1 por erro | URL + msg de erro |
| `api.ts:113` | `[API↺] 401 → retry com token fresco: ...` | só em 401 | URL |
| `providers.tsx:31` | `[NAV] /old → /new  Xms ⚠️ LENTO` | 1 por navegação | rotas |
| `providers.tsx:47` | `[QUERY✓] ["meals", ...]` | **1 por query bem-sucedida** | queryKey |
| `providers.tsx:51` | `[QUERY✗] ["..."]` | 1 por erro | queryKey + message |

Volume estimado em sessão típica de usuário ativo: ~50-100 logs/min no console. Polui DevTools dos usuários técnicos, custa CPU mínima e expõe queryKeys e rotas internas (info-disclosure menor).

Achado: AUD-020 (🟢) — gatear todos com `NODE_ENV === "development"` ou substituir por logger condicional.

## D.4 Discrepância de contrato no login

**Backend retorna** (`backend/app/api/v1/auth.py:47-50`):
```python
return TokenResponse(
    access_token=create_access_token(user.id),
    refresh_token=create_refresh_token(user.id),
)
```

`TokenResponse` (definido em `backend/app/schemas/user.py:46-50`) tem **apenas** `access_token`, `refresh_token`, `token_type`. **Sem `user`**.

**Frontend espera** (`frontend/app/api/auth/[...nextauth]/route.ts:64-70`):
```typescript
const data = await res.json();
return {
    id: String(data.user?.id ?? ""),                       // ← data.user é undefined → ""
    name: data.user?.name ?? credentials.email,            // ← cai no fallback
    email: credentials.email,
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
};
```

**Efeitos** (silenciosos, login funciona):
- `id` da sessão NextAuth fica como string vazia (`""`).
- `name` exibido na UI cai no fallback `credentials.email` — usuário vê o e-mail no lugar do nome até buscar `/auth/me` via `useUser()`.
- `accessToken`/`refreshToken` funcionam normalmente — autenticação não quebra.

**Por que não quebra:** o frontend não usa `session.user.id` em nenhuma lógica funcional (verificado com `grep -rn` em `app|components|lib` exceto build artefatos). Bug é puramente de qualidade de dado/UX (nome incorreto até refetch).

Achado: AUD-021 (🟠 alta).

**Correções possíveis** (escolher uma):
1. **Backend muda contrato** — adicionar campo `user` opcional em `TokenResponse`. Mais útil pro consumidor; aproveita a hidratação inicial.
2. **Frontend faz follow-up** — após `/auth/login` OK, o `authorize` busca `/auth/me` com o token recém-criado e popula `id`/`name` corretamente. 1 round-trip extra no login.

## D.5 TypeScript — usos de `any`

Comando: `rg -n ": any\b|as any\b" frontend/app frontend/components frontend/lib | grep -v test/mock/build`. Artefato: `artefatos/D5-any-usage.txt`.

| Arquivo:linha | Padrão | Origem |
|---|---|---|
| `components/dashboard/QuickAddModals.tsx:180` | `(window as any).SpeechRecognition || (window as any).webkitSpeechRecognition` | Web Speech API |
| `components/dashboard/QuickAddModals.tsx:187` | `rec.onresult = (e: any) => …` | Web Speech API |
| `components/dashboard/QuickAddModals.tsx:195` | `rec.onerror = (e: any) => …` | Web Speech API |
| `app/(dashboard)/refeicoes/page.tsx:445-463` | mesmos 3 padrões | Web Speech API (duplicado) |

**Total: 6 `any`, todos relacionados a `SpeechRecognition`** — todos duplicados entre `QuickAddModals.tsx` e `refeicoes/page.tsx`. Sem outros `any` no código de produção.

**Solução**: tipos `SpeechRecognition`, `SpeechRecognitionEvent`, `SpeechRecognitionErrorEvent` existem na DOM API (lib.dom.d.ts) mas `window.SpeechRecognition`/`window.webkitSpeechRecognition` precisam de module augmentation:

```ts
// types/speech.d.ts
declare global {
  interface Window {
    SpeechRecognition?: typeof SpeechRecognition;
    webkitSpeechRecognition?: typeof SpeechRecognition;
  }
}
export {};
```

Combinado com extração de `useVoiceCapture()` (já recomendado em AUD-018), elimina os 6 `any` e a duplicação simultaneamente.

Achado: AUD-022 (🟢) — cobertura de typing da Web Speech API.

## D.6 PWA / Service Worker

Arquivos: `frontend/public/sw.js` (18 LOC) e `frontend/app/manifest.ts` (44 LOC).

**`sw.js` — eventos**

| Evento | Estado | Comentário |
|---|---|---|
| `push` | ✅ | `title`, `body`, `icon` (192), `badge`, `vibrate`, `data.url` corretos |
| `notificationclick` | ✅ | `event.notification.close()` + `clients.openWindow(url)` |
| `install` (com `skipWaiting`) | ❌ | sem handler — atualizações de SW só ativam após **todas as tabs** serem fechadas |
| `activate` (com `clients.claim`) | ❌ | sem handler — primeiro carregamento exige reload manual para ganhar controle |
| `fetch` | — | inexistente — nenhuma estratégia offline (aceitável: app é online-first) |

**Manifest**

| Campo | Estado | Comentário |
|---|---|---|
| `name`, `short_name`, `description` | ✅ | |
| `start_url`, `display: standalone` | ✅ | |
| `background_color`, `theme_color` | ✅ | |
| `orientation: portrait-primary` | ✅ | |
| `shortcuts` (2) | ✅ | "Adicionar refeição", "Registrar água" — ótimo |
| Ícones | ⚠️ | Apenas 192 (`any`) e 512 (`maskable`). Faltam: 144, 384, e idealmente 512 com `any` separado |
| `apple-touch-icon` | ❌ | Não declarado (manifest icons não são lidos pelo iOS Safari) |
| `screenshots` | ❌ | Lighthouse recomenda para melhor UI de instalação |

**Achado:** AUD-023 (🟢) — gaps PWA em SW updates e cobertura de ícones.

## Notas e contexto

(texto livre conforme aprendizagens surgem)
