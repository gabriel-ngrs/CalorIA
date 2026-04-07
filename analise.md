# Análise de UI/UX — CalorIA

> Análise realizada em 07/04/2026 via navegação automatizada com Playwright.  
> Atualizada com deep pass (stress test completo) em 07/04/2026.  
> Prints disponíveis em `/prints/` (deep_01 a deep_46 para varredura profunda).

---

## Sumário

| # | Página | Print |
|---|--------|-------|
| 01 | Login | `01_login.png` |
| 02 | Cadastro | `02_register.png` |
| 03 | Dashboard | `03_dashboard.png` / `03b_dashboard_sem_popup.png` |
| 04 | Refeições (vazio) | `04_refeicoes.png` |
| 05 | Modal nova refeição — Texto | `05_refeicoes_modal_adicionar.png` |
| 06 | Modal nova refeição — Foto | `06_refeicoes_modal_foto.png` |
| 07 | Modal nova refeição — Áudio | `07_refeicoes_modal_audio.png` |
| 08 | Peso | `08_peso.png` |
| 09 | Hidratação | `09_hidratacao.png` |
| 10 | Humor & Energia | `10_humor.png` |
| 11 | Relatórios | `11_relatorios.png` |
| 12 | Lembretes | `12_lembretes.png` |
| 13 | Insights IA | `13_insights.png` |
| 14 | Perfil | `14_perfil.png` |
| 15 | Onboarding — Passo 1 | `15_onboarding.png` |
| 16 | Onboarding — Passo 2 | `16_onboarding_step2.png` |
| 17 | Dashboard — Modal via atalho | `17_dashboard_modal_texto.png` |

---

## Pontos Positivos

### 1. Identidade visual coerente
- Paleta verde-água (`#10B981`) bem definida e aplicada consistentemente em botões primários, links, indicadores ativos e badges.
- Ícones acompanham cada item de menu e cada seção de página, dando ritmo visual.
- Tipografia limpa, legível e sem exageros decorativos.

### 2. Sidebar de navegação funcional
- Menu lateral fixo com labels claros em português.
- Indicador de página ativa (ponto verde + fundo destacado) claro e imediato.
- Hierarquia visual adequada entre logo, nav e rodapé ("V0.1 Powered by Gabriel Negreiros").

### 3. Cards de macro no dashboard
- Os quatro cards (Calorias, Proteína, Carboidrato, Gordura) em grid 4 colunas são uma estrutura de mercado reconhecida (MyFitnessPal, Cronometer).
- Cada card tem cor diferenciada por macro, o que cria ancoragem visual eficiente.
- Barra de progresso + percentual + meta são informativos sem poluir.

### 4. Módulo de peso bem executado
- Gráfico de evolução 90 dias é o destaque da página — mostra tendência real de forma clara.
- Barra de progresso em direção à meta com % e valores absolutos ("86.2 → 78 kg") é excelente.
- Botões de ajuste rápido (−1, −0.5, −0.1, +0.1, +0.5, +1) são um padrão de UX mobile-first bem aplicado ao desktop.
- Histórico lateral com delta colorido (verde/vermelho) é leitura imediata.

### 5. Hidratação com atalhos práticos
- Botões pré-definidos (Copo 200ml, Garrafa P/M/G) reduzem o atrito de registro.
- Campo "Outro valor" com input livre é o escape certo para casos fora do padrão.
- Métricas laterais (Média diária, Dias com meta, Sequência) são motivadoras.

### 6. Modal de nova refeição multimodal
- Três formas de input (Texto, Foto, Áudio) atendem casos de uso diferentes e são uma diferenciação de produto relevante.
- Transição entre os modos é fluida e o modo ativo é claramente destacado.

### 7. Lembretes bem estruturados
- Formulário de criação completo (tipo, dias da semana, horários, mensagem).
- Lista de lembretes configurados na lateral com status e ação de disparo imediato.
- Seletor de dias da semana como chips clicáveis é o padrão correto para esse contexto.

### 8. Página de Insights IA bem organizada
- Seções bem divididas: "Hoje", "Análise de Período", "Relatórios", "Pergunte à IA".
- Cada ação tem um botão dedicado com label descritivo, evitando ambiguidade.
- O campo de pergunta livre com placeholder contextual é um bom incentivo ao uso.

### 9. Perfil com TDEE calculado
- Exibir o TDEE estimado no topo e compará-lo à meta calórica é informação de alto valor, pouco comum em apps do segmento.
- O card laranja de destaque para o TDEE cria hierarquia visual clara.

---

## Pontos Negativos e Problemas

### 1. Popup de "Ativar notificações" é invasivo e recorrente
- **Problema:** O popup aparece em TODAS as páginas visitadas, sem persistir o estado de rejeição. O usuário clica "Agora não" e ele retorna ao navegar para outra rota.
- **Impacto:** Alto — é o padrão anti-UX mais documentado em apps modernos. Interrompe a navegação em loop.
- **Padrão de mercado:** Notion, Linear, Vercel pedem notificação UMA vez por sessão e só voltam ao assunto se o usuário tocar em configurações. 
- **Sugestão:** Persistir o estado no `localStorage`/cookie. Se rejeitado, não reexibir por pelo menos 7 dias. Mover para Settings/Perfil como opção passiva.

### 2. Header exibe o e-mail completo como identificação do usuário
- **Problema:** `gabrielnegreirossaraiva38@gmail.com` ocupa ~280px no header, empurrando os botões de Notificação e Sair para a borda direita.
- **Impacto:** Médio — visual poluído, sem espaço para crescer (futuro badge de notificação, etc.), e o e-mail é uma informação sensível exposta permanentemente.
- **Padrão de mercado:** Apps como Strava, MyFitnessPal, Notion exibem nome do usuário ou avatar com inicial, nunca o e-mail cru.
- **Sugestão:** Exibir o `name` do usuário (ex: "Gabriel") com um avatar circular com inicial. E-mail fica acessível apenas no perfil ou tooltip.

### 3. Título do dashboard tem capitalização inconsistente e informal
- **Problema:** "Terça-Feira, 07 De Abril" usa capitalização de cada palavra (Title Case em português, que não é padrão da língua). O subtítulo "Resumo do seu dia" usa caixa correta.
- **Impacto:** Baixo, mas sinaliza inconsistência com as demais páginas.
- **Sugestão:** Usar `terça-feira, 07 de abril` (apenas primeiro caractere maiúsculo) ou `07 de Abril de 2026` — o segundo é mais formal e compatível com apps de saúde.

### 4. Seção "Registrar agora" no dashboard tem containers sem label nem borda
- **Problema:** Os três botões (Foto, Texto, Áudio) ficam dentro de containers que parecem cards quebrados — sem borda visível, sem fundo, sem separação clara. A área ao redor parece "incompleta" ou com CSS faltando.
- **Impacto:** Médio — passa impressão de trabalho inacabado. O usuário pode não perceber que são botões clicáveis.
- **Sugestão:** Aplicar fundo sutil (`bg-muted` ou borda `border-dashed`) nos containers, como nos modais. Ou unificar os três num único card com visual coeso.

### 5. Distribuição de macros (pizza chart) sem estado empty-state adequado
- **Problema:** Quando não há dados, a seção exibe apenas o texto "Sem dados hoje" sem nenhum elemento visual de orientação (ex: placeholder, ícone, call-to-action).
- **Impacto:** Médio — "Sem dados hoje" é funcional mas frio. Não convida o usuário a agir.
- **Sugestão:** Adicionar um estado vazio com ícone + texto motivador + botão "Registrar refeição". Padrão: Linear, Notion, Duolingo usam ilustrações leves em estados vazios para converter o usuário à ação.

### 6. Página de Relatórios: sidebar/nav some em viewports menores
- **Problema:** Na página de relatórios a navbar lateral desaparece visualmente (ela existe no DOM mas parece colapsar). O layout quebra em viewport ~1024px e as labels ficam sem espaço.
- **Impacto:** Alto para usuários com telas menores (laptops 13").
- **Sugestão:** Implementar sidebar colapsável com ícones apenas (icon-only mode) como fazem Vercel Dashboard, Linear, Notion. Ou usar navegação em hamburguer para telas < 1280px.

### 7. Página de Refeições: coluna lateral "Sem dados nutricionais" é muito magra
- **Problema:** A coluna direita com o resumo nutricional diário só tem ícone + dois textos cinzas quando não há refeições. O espaço é grande demais para tão pouca informação.
- **Impacto:** Baixo visualmente, mas prejudica a percepção de completude.
- **Sugestão:** Exibir os cards de macro zerados (0/meta) mesmo sem dados, mantendo a estrutura visual consistente com o dashboard.

### 8. Onboarding sem indicador de progresso numérico claro
- **Problema:** O stepper usa apenas bolinhas/traços sem rótulo ("Passo 1 de 2"). O usuário não sabe quantas etapas ainda existem.
- **Impacto:** Médio — estudos de UX (Baymard Institute) mostram que indicadores numéricos de progresso reduzem abandono em fluxos de onboarding em ~15-20%.
- **Sugestão:** Adicionar "1 de 2" ou "2 de 2" junto ao stepper. Opcional: nomear os passos ("Dados físicos → Metas").

### 9. Botão "Analisar com IA" no modal permanece visualmente ativo mesmo disabled
- **Problema:** O botão `Analisar com IA` está com `disabled` mas sua cor verde clara pode confundir — parece habilitado com pouco contraste. O padrão é usar `opacity: 0.5` + `cursor: not-allowed`, o que aqui não é tão perceptível.
- **Impacto:** Baixo/Médio — pode levar o usuário a clicar repetidamente sem feedback de por que não funciona.
- **Sugestão:** Aumentar contraste do disabled state (mais cinza, sem a cor verde) e adicionar tooltip ao passar o mouse explicando o motivo ("Digite o que comeu primeiro").

### 10. ~~Página de Humor: escala numérica (1–5) sem âncoras textuais~~ ✅ Falso positivo
- **Reavaliação (deep pass):** Os rótulos textuais ("Muito baixo", "Baixo", "Médio", "Alto", "Muito alto") já aparecem permanentemente abaixo de cada botão, tanto em estado normal quanto selecionado. O ponto negativo original estava incorreto.

### 11. Insights IA: resultado inline ✅ OK — mas latência crítica e 502 no chat
- **Reavaliação (deep pass):** Os resultados aparecem corretamente dentro do card de cada seção, expandindo-o. A área de resultado inline funciona.
- **Problema real 1:** As respostas da IA levam **10–24 segundos** (POST /api/v1/ai/insights: 10.8s; GET /api/v1/ai/patterns: 16.4s; GET /api/v1/ai/goal-adjustment: 23.6s), todas sinalizadas como ⚠️ LENTO no console. Não há skeleton/shimmer visível na área de resultado durante a espera.
- **Problema real 2:** O endpoint `POST /api/v1/ai/insights` retorna **502 Bad Gateway** ao usar "Pergunte à IA", deixando o campo sem resposta e sem mensagem de erro visível ao usuário.
- **Impacto:** Alto — usuário não sabe se o sistema travou ou está processando (10–24s sem feedback visual de progresso).
- **Sugestão:** Adicionar skeleton loader na área de resultado. Tratar o 502 com mensagem de erro contextual. Investigar timeout do servidor para chamadas longas à IA.

### 12. TanStack Query Devtools visível em produção/dev como ícone flutuante
- **Problema:** O ícone da ferramenta de desenvolvimento (canto inferior direito) está presente na interface. Embora seja para dev, em demo ou produção parece um bug/elemento estranho.
- **Impacto:** Baixo — cosmético, mas passa impressão de descuido.
- **Sugestão:** Condicionar a exibição a `process.env.NODE_ENV === 'development'` ou remover completamente do build de produção.

### 13. Logo "CalorIA" não tem ícone/marca visual própria
- **Problema:** A sidebar exibe só o texto "CalorIA" + subtítulo. Não há um logotipo, ícone ou símbolo de marca.
- **Impacto:** Médio — em apps de saúde, a identidade visual da marca no produto é um fator de confiança e profissionalismo. Apps como MyFitnessPal, Noom, Cronometer têm ícone + logotipo.
- **Sugestão:** Criar um símbolo simples (uma chama + folha, ou as letras C+IA estilizadas) para usar junto ao texto do logo.

---

## Bugs Adicionais — Deep Pass (07/04/2026)

### 14. Exclusão sem confirmação em Refeições E Lembretes
- **Problema:** Clicar no ícone de lixeira em qualquer item (refeição ou lembrete) dispara a exclusão imediata, sem nenhum diálogo de confirmação. Comportamento confirmado em ambas as páginas.
- **Impacto:** Alto — operação irreversível sem salvaguarda. O usuário pode excluir por engano itens de semanas atrás.
- **Sugestão:** Implementar `AlertDialog` de confirmação: "Tem certeza que deseja excluir? Esta ação não pode ser desfeita." Padrão universal de SaaS.

### 15. Formulários com validação nativa em inglês
- **Problema:** Os campos obrigatórios de `/login` e `/register` usam o atributo HTML `required`, exibindo tooltip nativo do browser ("Please fill out this field") em inglês, sem validação customizada em português.
- **Impacto:** Médio — quebra a experiência de produto em português e passa impressão de descuido.
- **Sugestão:** Implementar validação via `react-hook-form` + `zod` com mensagens em português ("Este campo é obrigatório", "E-mail inválido", etc.).

### 16. "Sugerir refeição" retorna erro
- **Problema:** O botão "Sugerir refeição" na página de Insights IA retorna erro ("Erro ao gerar sugestão. Tente novamente."). A API falha sem expor detalhes ao usuário.
- **Impacto:** Alto — funcionalidade principal completamente quebrada.
- **Sugestão:** Investigar o endpoint `/api/v1/ai/meal-suggestion`. Verificar se o modelo Gemini recebe contexto suficiente (calorias restantes do dia) e se a resposta está sendo parseada corretamente.

### 17. Modal de edição de refeição não permite editar itens alimentares
- **Problema:** Ao editar uma refeição já registrada, o modal só permite alterar o tipo da refeição e notas. Não é possível editar, remover ou adicionar alimentos individuais ao `MealItem`.
- **Impacto:** Médio — o usuário precisa excluir e recriar a refeição inteira para corrigir um alimento.
- **Sugestão:** Adicionar lista editável de `MealItems` no modal de edição.

### 18. "Sequência atual" sem espaço entre número e unidade
- **Problema:** Na página de Hidratação, o card lateral exibe "0dias" sem espaço entre o número e a unidade (deveria ser "0 dias").
- **Impacto:** Baixo — cosmético mas passa impressão de bug de formatação.
- **Sugestão:** Adicionar espaço no template string ou usar formatação separada para número e unidade.

### 19. Perfil e Humor salvam sem feedback visual de sucesso
- **Problema:** Ao clicar em "Salvar alterações" no Perfil ou "Registrar" no Humor, a ação é executada com sucesso mas nenhum toast de confirmação aparece. O único feedback é a atualização silenciosa dos dados.
- **Impacto:** Médio — o usuário fica em dúvida se a ação funcionou.
- **Sugestão:** Adicionar toast de sucesso ("Perfil atualizado!", "Humor registrado!") consistente com o padrão já usado em outras partes do app.

### 20. Relatórios: título do gráfico de calorias hardcoded como "últimos 7 dias"
- **Problema:** O título "Calorias — últimos 7 dias" não atualiza quando o filtro de período é alterado para 14d ou 30d. Os dados do gráfico mudam corretamente, mas o título permanece fixo.
- **Impacto:** Baixo — inconsistência cosmética mas confunde sobre o período visualizado.
- **Sugestão:** Tornar o título dinâmico baseado no período selecionado: `\`Calorias — últimos ${period} dias\``.

### 21. Insights: "Alertas nutricionais" exibe "nos últimos 0 dias"
- **Problema:** Após clicar em "Verificar alertas" com período 14d selecionado, o texto do resultado exibe "Nenhuma deficiência significativa detectada nos últimos **0 dias**." em vez de "14 dias".
- **Impacto:** Baixo — o valor correto deveria vir do contexto da requisição mas provavelmente o backend está retornando 0 quando não há dados no período.
- **Sugestão:** Verificar se o backend passa o período correto na resposta e se o frontend usa o período da resposta ou o período selecionado na UI.

### 22. "Pergunte à IA" retorna 502 Bad Gateway
- **Problema:** O campo de chat livre "Pergunte à IA" envia para `POST /api/v1/ai/insights` e recebe HTTP 502 Bad Gateway, sem nenhuma mensagem de erro visível ao usuário (o input simplesmente não responde).
- **Impacto:** Alto — a funcionalidade de chat com IA está completamente inoperante.
- **Sugestão:** Corrigir o endpoint. Adicionar tratamento de erro no frontend para exibir mensagem quando a requisição falha.

### 23. "Pergunte à IA": botão de envio sem aria-label
- **Problema:** O botão de envio do chat tem `type="submit"`, ícone de seta, mas sem texto visível e sem `aria-label`. É invisível para leitores de tela.
- **Impacto:** Baixo para usuários comuns, alto para acessibilidade.
- **Sugestão:** Adicionar `aria-label="Enviar pergunta"` ao botão.

### 24. Lembretes: "Repetir de X em X horas" é positivo — documentado
- **Nota:** O modo "Repetir de X em X horas" tem UX excelente: mostra preview em tempo real de todos os horários que serão criados ("8 lembretes serão criados: 08:00, 10:00...") e atualiza o botão dinamicamente ("Criar 8 lembretes"). Referência de produto a manter.

---

## O que Está Fora do Padrão de Mercado

| Item | Padrão atual | Padrão de mercado |
|------|-------------|-------------------|
| Identificação de usuário no header | E-mail completo | Nome + avatar |
| Popup de notificação | Reaparece em toda navegação | Uma vez por sessão |
| Empty state de gráficos | Texto simples | Ilustração + CTA |
| Stepper do onboarding | Bolinhas sem numeração | "1 de 2" com nomes |
| Disabled button | Verde claro com pouco contraste | Cinza com `cursor: not-allowed` |
| Logo na sidebar | Texto puro | Ícone + texto |
| Devtools em UI | Visível (ícone flutuante) | Invisível/oculto |
| Exclusão de itens | Imediata, sem confirmação | AlertDialog de confirmação |
| Validação de formulários | HTML nativo em inglês | Biblioteca (zod/RHF) em português |
| Feedback após salvar | Silencioso | Toast de sucesso |
| Latência de IA | 10–24s sem indicador visual | Skeleton loader + progress |
| Chat com IA ("Pergunte") | 502 / sem resposta | Funcionando com fallback de erro |

---

## Prioridade de Correções Sugeridas

| Prioridade | Item |
|-----------|------|
| 🔴 Alta | "Pergunte à IA" retorna 502 — chat inoperante (#22) |
| 🔴 Alta | "Sugerir refeição" sempre retorna erro (#16) |
| 🔴 Alta | Exclusão sem confirmação — refeições e lembretes (#14) |
| 🔴 Alta | Popup de notificação recorrente em toda navegação (#1) |
| 🔴 Alta | Header com e-mail cru → nome + avatar (#2) |
| 🟡 Média | Validação de formulários em inglês → português (#15) |
| 🟡 Média | Latência IA 10–24s sem skeleton loader (#11) |
| 🟡 Média | Feedback silencioso ao salvar Perfil e Humor (#19) |
| 🟡 Média | Botões "Registrar agora" sem container visual (#4) |
| 🟡 Média | Empty states com CTA em vez de texto simples (#5) |
| 🟡 Média | Onboarding com indicador numérico de progresso (#8) |
| 🟡 Média | Sidebar colapsável para telas menores (#6) |
| 🟡 Média | Modal de edição não permite editar alimentos (#17) |
| 🟢 Baixa | Título do gráfico hardcoded "últimos 7 dias" (#20) |
| 🟢 Baixa | "Alertas nutricionais" exibe "0 dias" (#21) |
| 🟢 Baixa | "Sequência atual 0dias" — falta espaço (#18) |
| 🟢 Baixa | Capitalização do título do dashboard (#3) |
| 🟢 Baixa | Disabled button com contraste mais claro (#9) |
| 🟢 Baixa | Devtools oculto em produção (#12) |
| 🟢 Baixa | Logo com símbolo de marca (#13) |
| 🟢 Baixa | Botão "Pergunte à IA" sem aria-label (#23) |

---

## Avaliação Geral

O CalorIA tem uma base sólida de UI — paleta consistente, estrutura de navegação clara e componentes funcionais em todas as páginas principais. O produto está claramente acima de um MVP "feio" e já demonstra cuidado visual real.

**Deep pass (07/04/2026) — novos achados:** A varredura mais profunda revelou bugs funcionais críticos que não aparecem em uma análise visual: o chat "Pergunte à IA" retorna 502, "Sugerir refeição" está quebrada, exclusão de itens é imediata sem confirmação em todas as entidades, e as respostas de IA levam 10–24 segundos sem feedback visual de progresso. Adicionalmente, foi corrigido um falso positivo da análise inicial: os rótulos da escala de Humor já são permanentemente visíveis.

Pontos positivos confirmados no stress test: o modo "Repetir de X em X horas" nos Lembretes tem UX excelente com preview em tempo real, todos os outros botões de IA (exceto chat e sugestão de refeição) funcionam corretamente, e o sistema de pausa/retomada de lembretes é bem implementado.

Os problemas identificados são uma mistura de **bugs funcionais** (alta prioridade) e **polish de interação** (média/baixa prioridade). Com as correções críticas aplicadas, o app ficaria em nível comparável ao de produtos SaaS de saúde early-stage no mercado (ex: MacroFactor, Carbon Diet Coach).

O diferencial mais forte atualmente é a **multimodalidade do registro** (texto + foto + áudio), o **módulo de peso com gráfico 90 dias** e os **Insights IA funcionais** — todos acima da média do segmento.
