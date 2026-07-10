"""Storage com URLs assinadas (S3/R2).

Chaves nunca vao ao cliente: uploads e entregaveis sao acessados via URL
assinada de curta duracao. Se as credenciais nao estiverem configuradas
(dev/testes), cai num stub que devolve uma URL local previsivel.
"""
import uuid
from functools import lru_cache

from app.config import settings


@lru_cache
def _client(endpoint: str | None = None):
    if not (settings.storage_access_key and settings.storage_secret_key):
        return None
    import boto3  # import tardio: so quando ha credenciais
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=endpoint or settings.storage_endpoint_url,
        region_name=settings.storage_region,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        config=Config(signature_version="s3v4"),
    )


def _internal_client():
    """Cliente para acesso server-side (api/worker) — usa o endpoint interno."""
    return _client(settings.storage_endpoint_url)


def _public_client():
    """Cliente para gerar URLs assinadas que o NAVEGADOR vai acessar.

    Em dev local (MinIO) o navegador acessa por localhost, enquanto os
    containers acessam por 'minio'. STORAGE_PUBLIC_ENDPOINT_URL cobre esse caso;
    se nao definido, usa o mesmo endpoint interno (ex.: S3/R2 em producao).
    """
    return _client(settings.storage_public_endpoint_url or settings.storage_endpoint_url)


def new_key(project_id: uuid.UUID, kind: str, ext: str) -> str:
    return f"projects/{project_id}/{kind}/{uuid.uuid4().hex}.{ext.lstrip('.')}"


def presign_put(key: str, content_type: str) -> str:
    """URL assinada para upload (PUT)."""
    client = _public_client()
    if client is None:
        return f"https://storage.local/{settings.storage_bucket}/{key}?op=put"
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.storage_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=settings.storage_signing_ttl,
    )


def presign_get(key: str) -> str:
    """URL assinada para download (GET)."""
    client = _public_client()
    if client is None:
        return f"https://storage.local/{settings.storage_bucket}/{key}?op=get"
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.storage_bucket, "Key": key},
        ExpiresIn=settings.storage_signing_ttl,
    )


# --------------------------------------------------------------------------- #
# Acesso server-side (workers) — nunca exposto ao cliente.
# --------------------------------------------------------------------------- #
class StorageNotConfigured(Exception):
    pass


def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Sobe bytes diretamente (worker). Retorna a chave."""
    client = _internal_client()
    if client is None:
        raise StorageNotConfigured("Credenciais de storage ausentes (STORAGE_ACCESS_KEY/SECRET)")
    client.put_object(
        Bucket=settings.storage_bucket, Key=key, Body=data, ContentType=content_type
    )
    return key


def get_bytes(key: str) -> bytes:
    """Baixa bytes de um asset (worker)."""
    client = _internal_client()
    if client is None:
        raise StorageNotConfigured("Credenciais de storage ausentes (STORAGE_ACCESS_KEY/SECRET)")
    obj = client.get_object(Bucket=settings.storage_bucket, Key=key)
    return obj["Body"].read()
