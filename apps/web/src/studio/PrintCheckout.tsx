import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";
import type { PrintAddress, PrintOrder } from "../types";

function money(cents: number | null): string {
  if (cents == null) return "—";
  return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

const emptyAddress: PrintAddress = {
  recipient_name: "",
  postal_code: "",
  street: "",
  number: "",
  complement: "",
  district: "",
  city: "",
  state: "",
};

/** Endereço, frete e pagamento do impresso. O gateway só abre quando estiver configurado. */
export function PrintCheckout({ projectId }: { projectId: string }) {
  const [order, setOrder] = useState<PrintOrder | null>(null);
  const [address, setAddress] = useState<PrintAddress>(emptyAddress);
  const [installments, setInstallments] = useState(1);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    api
      .printOrder(projectId)
      .then((next) => {
        if (cancel) return;
        setOrder(next);
        setAddress({
          recipient_name: next.recipient_name ?? "",
          postal_code: next.postal_code ?? "",
          street: next.street ?? "",
          number: next.number ?? "",
          complement: next.complement ?? "",
          district: next.district ?? "",
          city: next.city ?? "",
          state: next.state ?? "",
        });
      })
      .catch((err: Error) => {
        if (!cancel) setNote(err.message);
      });
    return () => {
      cancel = true;
    };
  }, [projectId]);

  async function saveAddress(ev: FormEvent) {
    ev.preventDefault();
    setNote(null);
    try {
      setOrder(await api.savePrintAddress(projectId, address));
    } catch (err) {
      setNote(err instanceof Error ? err.message : "Endereço inválido.");
    }
  }

  async function quote() {
    setNote(null);
    try {
      setOrder(await api.quotePrintFreight(projectId));
    } catch (err) {
      setNote(err instanceof Error ? err.message : "Frete indisponível.");
    }
  }

  async function choose(serviceId: number) {
    setNote(null);
    try {
      setOrder(await api.selectPrintFreight(projectId, serviceId));
    } catch (err) {
      setNote(err instanceof Error ? err.message : "Não foi possível escolher o frete.");
    }
  }

  async function pay() {
    setNote(null);
    try {
      const next = await api.checkoutPrint(projectId, installments);
      setOrder(next);
      if (next.checkout_url) window.location.assign(next.checkout_url);
    } catch (err) {
      setNote(err instanceof Error ? err.message : "Pagamento indisponível.");
    }
  }

  if (!order) return note ? <p className="muted">{note}</p> : null;

  return (
    <div style={{ marginTop: 12 }}>
      <p className="muted">
        {order.code}
        {order.book_price_cents != null ? ` · Livro ${money(order.book_price_cents)}` : ""}
        {order.block_reason ? ` · ${order.block_reason}` : ""}
      </p>
      {order.tracking_code && <p role="status">Rastreio {order.tracking_code}</p>}
      <form onSubmit={(ev) => void saveAddress(ev)} style={{ display: "grid", gap: 8, marginTop: 8 }}>
        <label>
          Nome
          <input
            value={address.recipient_name}
            onChange={(e) => setAddress({ ...address, recipient_name: e.target.value })}
          />
        </label>
        <label>
          CEP
          <input
            value={address.postal_code}
            onChange={(e) => setAddress({ ...address, postal_code: e.target.value })}
          />
        </label>
        <label>
          Rua
          <input value={address.street} onChange={(e) => setAddress({ ...address, street: e.target.value })} />
        </label>
        <label>
          Número
          <input value={address.number} onChange={(e) => setAddress({ ...address, number: e.target.value })} />
        </label>
        <label>
          Bairro
          <input
            value={address.district}
            onChange={(e) => setAddress({ ...address, district: e.target.value })}
          />
        </label>
        <label>
          Cidade
          <input value={address.city} onChange={(e) => setAddress({ ...address, city: e.target.value })} />
        </label>
        <label>
          UF
          <input
            value={address.state}
            maxLength={2}
            onChange={(e) => setAddress({ ...address, state: e.target.value })}
          />
        </label>
        <button type="submit">Salvar endereço</button>
      </form>
      <button type="button" style={{ marginTop: 8 }} onClick={() => void quote()}>
        Calcular frete
      </button>
      {(order.freight_options ?? []).length > 0 && (
        <ul>
          {order.freight_options.map((item) => (
            <li key={item.service_id}>
              <button type="button" onClick={() => void choose(item.service_id)}>
                {item.service_name} · {money(item.price_cents)}
                {item.delivery_days == null ? " · prazo não informado" : ` · ${item.delivery_days} dias`}
              </button>
            </li>
          ))}
        </ul>
      )}
      <label style={{ display: "block", marginTop: 8 }}>
        Parcelas
        <select value={installments} onChange={(e) => setInstallments(Number(e.target.value))}>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              {n}x
            </option>
          ))}
        </select>
      </label>
      <button type="button" disabled={!order.checkout_available} onClick={() => void pay()}>
        Pagar impresso
      </button>
      {!order.checkout_available && (
        <p className="muted">O gateway de pagamento ainda não foi escolhido. O pedido segue como cotação.</p>
      )}
      {note && <p className="muted">{note}</p>}
    </div>
  );
}
