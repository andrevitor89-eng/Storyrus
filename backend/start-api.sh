#!/usr/bin/env sh
# Start da API no Render: roda as migracoes e sobe o uvicorn.
# Usa "python -m" para nao depender de scripts no PATH.
set -e
python -m alembic upgrade head
# O worker separado hiberna no plano free. Este processo, que o Studio
# mantém acordado, também consome a fila da prévia.
export EMBED_WORKER=true
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
