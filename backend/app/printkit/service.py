"""Pedido impresso: arquivo único de capa e miolo. Nota, frete e pagamento ficam fechados."""

from __future__ import annotations

import io
import json
import uuid
import zipfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.config import settings
from app.models import Asset, AssetKind, PrintOrder, Project, _now
from app.printkit.files import build_print_pdf
from app.printkit.pricing import book_price_cents
from app.printkit.spec import INTERIOR_PAGES, PrintPagesMissing, PrintSpecIncomplete, spec_from_settings

_FILE_STATUSES = frozenset(
    {"files_ready", "sent_for_validation", "approved", "rejected"}
)
_FORWARD = {
    "files_ready": frozenset({"sent_for_validation"}),
    "sent_for_validation": frozenset({"approved", "rejected"}),
}


class FulfillmentPending(Exception):
    """Nota, coleta e faturamento ainda não fecham o envio à gráfica."""

    gaps = ("fiscal", "logistics", "billing")

    def __init__(self) -> None:
        super().__init__(
            "Nota fiscal, coleta e faturamento ainda não estão fechados. O pedido não segue para a gráfica."
        )


def order_code(order_id: uuid.UUID) -> str:
    return "SR-" + order_id.hex[:8].upper()


def get_print_order(db: Session, project_id: uuid.UUID) -> PrintOrder | None:
    return db.scalar(select(PrintOrder).where(PrintOrder.project_id == project_id))


def invalidate_print(db: Session, project: Project) -> None:
    """Livro refeito: o pacote antigo deixa de valer, salvo se o impresso já foi pago."""
    order = get_print_order(db, project.id)
    if order is None or order.payment_status != "paid":
        project.print_requested_at = None
        project.print_status = None
    if order is None or order.payment_status == "paid":
        return
    order.file_key = None
    order.status = "awaiting_spec"
    order.block_reason = None
    order.freight_options = None
    order.freight_service_id = None
    order.freight_service_name = None
    order.freight_price_cents = None
    order.freight_days = None
    order.payment_status = "unpaid"
    order.payment_provider = None
    order.payment_reference = None
    order.amount_cents = None
    order.label_error = None


def _sync(project: Project, order: PrintOrder) -> None:
    project.print_status = order.status


def _page_images(db: Session, project: Project) -> list[bytes]:
    rows = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
        .order_by(Asset.created_at.asc())
    ).all()
    ordered = sorted(rows, key=lambda row: int((row.meta or {}).get("page") or 0))
    images: list[bytes] = []
    for row in ordered:
        try:
            images.append(storage.get_bytes(row.storage_key))
        except Exception:
            continue
    return images


def _store_pdf(project_id: uuid.UUID, kind: str, blob: bytes) -> str:
    key = storage.new_key(project_id, kind, "pdf")
    storage.put_bytes(key, blob, "application/pdf")
    return key


def _clear_file(order: PrintOrder) -> None:
    order.file_key = None


def prepare_files(db: Session, project: Project, order: PrintOrder) -> None:
    """Gera um PDF com capa e 16 páginas. Sem spec completa, não publica arquivo."""
    if order.status in {"sent_for_validation", "approved"} or order.payment_status == "paid":
        return
    order.book_size = project.book_size
    order.cover_type = project.cover_type
    order.quantity = 1
    if order.book_size not in {"P", "M"} or order.cover_type not in {"soft", "hard"}:
        order.status = "awaiting_spec"
        order.block_reason = "Tamanho ou tipo de capa ausente no projeto."
        _clear_file(order)
        _sync(project, order)
        return
    if (
        order.book_size == "P"
        and order.cover_type == "hard"
        and not settings.print_allow_p_hardcover
    ):
        order.status = "held"
        order.block_reason = "15 × 15 cm em capa dura ainda não foi liberado pela produção."
        _clear_file(order)
        _sync(project, order)
        return
    spec = spec_from_settings()
    gaps = spec.missing(order.cover_type)
    if gaps:
        order.status = "awaiting_spec"
        order.block_reason = "Especificação de produção incompleta: " + ", ".join(gaps)
        _clear_file(order)
        _sync(project, order)
        return
    pages = _page_images(db, project)
    if len(pages) != INTERIOR_PAGES:
        order.status = "awaiting_pages"
        order.block_reason = f"O miolo impresso precisa de {INTERIOR_PAGES} páginas."
        _clear_file(order)
        _sync(project, order)
        return
    try:
        blob = build_print_pdf(
            order_code=order.code,
            book_size=order.book_size,
            cover_type=order.cover_type,
            spec=spec,
            interior_pages=pages,
        )
    except PrintPagesMissing:
        order.status = "awaiting_pages"
        order.block_reason = f"O miolo impresso precisa de {INTERIOR_PAGES} páginas."
        _clear_file(order)
        _sync(project, order)
        return
    except PrintSpecIncomplete as exc:
        order.status = "awaiting_spec"
        order.block_reason = str(exc)
        _clear_file(order)
        _sync(project, order)
        return
    order.file_key = _store_pdf(project.id, "print_file", blob)
    order.status = "files_ready"
    order.block_reason = None
    _sync(project, order)


def open_print_order(db: Session, project: Project) -> PrintOrder:
    order = get_print_order(db, project.id)
    if order is None:
        order_id = uuid.uuid4()
        order = PrintOrder(
            id=order_id,
            project_id=project.id,
            code=order_code(order_id),
            quantity=1,
            status="awaiting_spec",
            payment_status="unpaid",
        )
        db.add(order)
        db.flush()
    if project.print_requested_at is None:
        project.print_requested_at = _now()
    prepare_files(db, project, order)
    _sync(project, order)
    return order


def package_zip(order: PrintOrder) -> bytes:
    if not order.file_key:
        raise FileNotFoundError(order.code)
    spec = spec_from_settings()
    file_name = spec.file_name(order.code)
    manifest = {
        "code": order.code,
        "book_size": order.book_size,
        "cover_type": order.cover_type,
        "quantity": order.quantity,
        "interior_pages": INTERIOR_PAGES,
        "files": {"livro": file_name},
        "pdf_x": spec.pdf_x,
        "color_profile": spec.color_profile,
        "production_ready": order.status in _FILE_STATUSES,
        "fulfillment_blockers": list(FulfillmentPending.gaps),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(file_name, storage.get_bytes(order.file_key))
        archive.writestr(
            "pedido.json",
            json.dumps(manifest, ensure_ascii=False).encode("utf-8"),
        )
    return buf.getvalue()


def advance_validation(order: PrintOrder, target: str) -> None:
    allowed = _FORWARD.get(order.status, frozenset())
    if target not in allowed:
        raise ValueError(order.status)
    order.status = target
    if order.project is not None:
        _sync(order.project, order)


def address_complete(order: PrintOrder) -> bool:
    postal = "".join(ch for ch in (order.postal_code or "") if ch.isdigit())
    return bool(
        (order.recipient_name or "").strip()
        and len(postal) == 8
        and (order.street or "").strip()
        and (order.number or "").strip()
        and (order.district or "").strip()
        and (order.city or "").strip()
        and len((order.state or "").strip()) == 2
    )


def apply_address(order: PrintOrder, data: dict) -> None:
    order.recipient_name = data["recipient_name"].strip()
    order.postal_code = "".join(ch for ch in data["postal_code"] if ch.isdigit())
    order.street = data["street"].strip()
    order.number = data["number"].strip()
    order.complement = (data.get("complement") or "").strip() or None
    order.district = data["district"].strip()
    order.city = data["city"].strip()
    order.state = data["state"].strip().upper()


def quote_order(order: PrintOrder):
    raise FulfillmentPending()


def select_freight(order: PrintOrder, service_id: int) -> None:
    raise FulfillmentPending()


def start_checkout(order: PrintOrder, installments: int):
    raise FulfillmentPending()


def fulfill_payment(db: Session, order: PrintOrder) -> None:
    raise FulfillmentPending()


def price_for(order: PrintOrder) -> int | None:
    try:
        return book_price_cents(order.book_size)
    except ValueError:
        return None
