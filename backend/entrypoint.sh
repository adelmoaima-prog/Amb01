#!/usr/bin/env bash
set -e

echo "Aguardando banco de dados..."
until python -c "
import asyncio, asyncpg, os, sys
async def check():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg', 'postgresql')
    try:
        conn = await asyncpg.connect(url)
        await conn.close()
    except Exception as e:
        sys.exit(1)
asyncio.run(check())
" 2>/dev/null; do
  sleep 2
done
echo "Banco disponível."

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
