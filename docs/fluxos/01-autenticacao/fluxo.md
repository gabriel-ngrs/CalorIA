# Fluxo de Autenticacao

## Visao Geral

O CalorIA usa JWT (JSON Web Tokens) para autenticacao. O frontend usa NextAuth como intermediario, e o backend FastAPI emite e valida os tokens.

---

## 1. Login

1. Usuario informa email + senha no frontend (`/login`)
2. NextAuth chama `POST /api/v1/auth/login` no backend
3. Backend busca usuario no banco por email
4. Valida senha com `bcrypt.verify(senha, hash)`
5. Se valido: gera `access_token` (30min) + `refresh_token`
6. Retorna tokens + dados do usuario
7. NextAuth armazena tokens no JWT session
8. Frontend redireciona para `/dashboard`
9. Se invalido: retorna 401, frontend exibe erro

---

## 2. Registro de Usuario

1. Usuario preenche nome, email, senha em `/register`
2. Frontend chama `POST /api/v1/auth/register`
3. Backend verifica se email ja existe → 409 se sim
4. Faz hash da senha com bcrypt
5. Insere usuario no banco
6. Gera tokens e retorna
7. NextAuth armazena e redireciona para `/dashboard`

---

## 3. Refresh de Token

O access token expira em 30 minutos. O frontend renova proativamente ~2 minutos antes.

1. Request interceptor (`api.ts`) verifica cache de token em memoria
2. Se token expira em < 2 minutos: dispara refresh
3. Chama `getSession()` que aciona callback JWT do NextAuth
4. NextAuth chama `POST /api/v1/auth/refresh` com o refresh_token
5. Backend valida e retorna novos tokens
6. NextAuth atualiza session, frontend atualiza cache
7. Proximo request usa o novo token

**Deduplicacao:** Se multiplos requests disparam sem cache, apenas UMA chamada `getSession()` e feita e compartilhada via Promise (`_pendingSession`).

---

## 4. Logout

1. Usuario clica "Sair"
2. Frontend chama `POST /api/v1/auth/logout` com refresh_token
3. Backend adiciona refresh_token a blacklist no Redis
4. NextAuth executa `signOut()` — limpa session e cookies
5. Frontend redireciona para `/login`

---

## 5. Ciclo de Vida

- **Nao autenticado** → Login ou Registro → **Autenticado**
- **Autenticado** → Refresh automatico a cada ~28 min
- **Autenticado** → Logout → **Nao autenticado**
- **Autenticado** → Refresh falha (token expirado) → **Nao autenticado**

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `frontend/app/(auth)/login/page.tsx` | UI de login |
| `frontend/app/(auth)/register/page.tsx` | UI de registro |
| `frontend/app/api/auth/[...nextauth]/route.ts` | Configuracao NextAuth |
| `frontend/lib/api.ts` | Interceptor com refresh proativo |
| `backend/app/api/v1/auth.py` | Endpoints login, register, refresh, logout |
| `backend/app/core/security.py` | Criacao e validacao de JWT |
| `backend/app/services/user_service.py` | Logica de criacao e autenticacao |
| `backend/app/services/auth_service.py` | Blacklist de tokens |
