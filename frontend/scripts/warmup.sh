#!/bin/sh
# Pré-compila as rotas mais acessadas logo após o Next.js iniciar.
# Executa em background enquanto o servidor está rodando.
# Resultado: primeira visita do usuário já encontra as rotas compiladas.

TRIES=0
MAX_TRIES=40  # 80 segundos de espera máxima

echo "[warmup] Aguardando Next.js ficar pronto..."
until wget -qO- http://localhost:3000 >/dev/null 2>&1; do
  sleep 2
  TRIES=$((TRIES + 1))
  if [ "$TRIES" -ge "$MAX_TRIES" ]; then
    echo "[warmup] Timeout aguardando Next.js. Abortando pré-compilação."
    exit 0
  fi
done

echo "[warmup] Next.js pronto. Pré-compilando rotas críticas..."

# /login — rota mais acessada, mais pesada de compilar (~4-5s)
wget -qO- http://localhost:3000/login >/dev/null 2>&1
echo "[warmup] /login compilado."

# /api/auth — necessário para sessão funcionar
wget -qO- http://localhost:3000/api/auth/providers >/dev/null 2>&1
echo "[warmup] /api/auth compilado."

echo "[warmup] Pré-compilação concluída. App pronto para uso."
