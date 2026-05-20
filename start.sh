#!/usr/bin/env bash
set -e

# ─── Gera .env se não existir ───────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "▶ Criando arquivo .env..."
  cp .env.example .env

  # Gera FERNET_KEY automaticamente
  FERNET_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null \
    || python  -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')

  if [ -n "$FERNET_KEY" ]; then
    sed -i "s|^FERNET_KEY=.*|FERNET_KEY=${FERNET_KEY}|" .env
    echo "  ✓ FERNET_KEY gerado"
  else
    echo "  ⚠ Instale a lib 'cryptography' para gerar FERNET_KEY:"
    echo "    pip install cryptography"
    exit 1
  fi
fi

# ─── Sobe os serviços ────────────────────────────────────────────────────────
echo "▶ Construindo e subindo serviços (pode levar alguns minutos)..."
docker compose up --build -d

# ─── Aguarda o banco ficar pronto ───────────────────────────────────────────
echo "▶ Aguardando banco de dados..."
until docker compose exec -T postgres pg_isready -U ambuser -d ambulatorio -q 2>/dev/null; do
  sleep 2
done
echo "  ✓ Banco disponível"

# ─── Seed data (apenas se ainda não houver usuários) ────────────────────────
USERS=$(docker compose exec -T postgres psql -U ambuser -d ambulatorio -tAc \
  "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

if [ "$USERS" = "0" ] || [ -z "$USERS" ]; then
  echo "▶ Carregando dados demo (≈ 11.000 consultas)..."
  docker compose exec -T backend python -m app.seed.seed_data
  echo "  ✓ Seed concluído"
else
  echo "  ✓ Dados já existem ($USERS usuários encontrados)"
fi

# ─── Pronto ─────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   HUC Ambulatorial rodando em http://localhost   ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Login:  admin@huc.br                            ║"
echo "║  Senha:  Admin@2024                              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Parar:    docker compose down"
echo "Logs:     docker compose logs -f"
