import { FormEvent, useCallback, useEffect, useState } from "react";
import logo from "./assets/logo.png";
import { api } from "./api";
import type { OrderTicket } from "./types";
import "./usage.css";

const STORAGE_KEY = "storyrus.usage.password";

function when(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

function titleOf(summary: string): string {
  return summary.split("\n")[0]?.trim() || "Pedido";
}

function fieldsOf(order: OrderTicket): { label: string; value: string }[] {
  const rows = order.summary
    .split("\n")
    .slice(1)
    .map((line) => {
      const cut = line.indexOf(":");
      if (cut === -1) return { label: line, value: "" };
      return { label: line.slice(0, cut).trim(), value: line.slice(cut + 1).trim() };
    })
    .filter((row) => row.label);
  if (order.child_age != null) rows.push({ label: "Idade", value: String(order.child_age) });
  if (order.book_size === "M" || order.book_size === "P") {
    rows.push({
      label: "Tamanho",
      value: order.book_size === "P" ? "P — 15 × 15 cm" : "M — 20 × 20 cm",
    });
  }
  if (order.cover_type === "soft" || order.cover_type === "hard") {
    rows.push({
      label: "Capa",
      value: order.cover_type === "soft" ? "Capa mole" : "Capa dura",
    });
  }
  return rows;
}

export function Pedidos() {
  const [password, setPassword] = useState(() => sessionStorage.getItem(STORAGE_KEY) ?? "");
  const [draft, setDraft] = useState("");
  const [orders, setOrders] = useState<OrderTicket[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (secret: string) => {
    setLoading(true);
    setError(null);
    try {
      const report = await api.usage(secret);
      const list = report.orders ?? [];
      setOrders(list);
      setSelected((cur) => (cur && list.some((order) => order.id === cur) ? cur : list[0]?.id ?? null));
      sessionStorage.setItem(STORAGE_KEY, secret);
      setPassword(secret);
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      if (status === 401) {
        sessionStorage.removeItem(STORAGE_KEY);
        setPassword("");
        setOrders(null);
        setError("Senha inválida.");
      } else if (status === 429) {
        sessionStorage.removeItem(STORAGE_KEY);
        setPassword("");
        setOrders(null);
        setError("Muitas tentativas. Aguarde e tente de novo.");
      } else if (status === 503) {
        setError("Painel ainda não configurado no servidor.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao carregar pedidos.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (password) void load(password);
  }, [password, load]);

  function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    const next = draft.trim();
    if (next) void load(next);
  }

  const current = orders?.find((order) => order.id === selected) ?? null;

  if (!password || (error && !orders)) {
    return (
      <div className="usage">
        <div className="usage-gate card auth">
          <img className="auth-logo" src={logo} alt="Story R Us" />
          <h1>Pedidos</h1>
          <p className="muted">Página privada. Use a mesma senha do painel de gastos.</p>
          <form onSubmit={onSubmit}>
            <label>
              Senha
              <input
                type="password"
                autoComplete="current-password"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
              />
            </label>
            <button type="submit" disabled={!draft.trim() || loading}>
              {loading ? "Entrando…" : "Entrar"}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="usage">
      <header className="usage-head">
        <img className="hdr-logo" src={logo} alt="Story R Us" />
        <div>
          <h1>Pedidos</h1>
          <p className="muted">Cada livro enviado com foto. Abra um item para ver o pedido inteiro.</p>
        </div>
        <button
          className="link"
          type="button"
          onClick={() => {
            sessionStorage.removeItem(STORAGE_KEY);
            setPassword("");
            setOrders(null);
            setDraft("");
          }}
        >
          Sair
        </button>
      </header>

      {error && <p className="error">{error}</p>}

      {(orders ?? []).length === 0 ? (
        <p className="muted">Nenhum pedido ainda. O pedido aparece depois que a família cria o livro e a foto chega.</p>
      ) : (
        <div className="usage-orders">
          <ul className="usage-order-list" aria-label="Lista de pedidos">
            {(orders ?? []).map((order) => (
              <li key={order.id}>
                <button
                  type="button"
                  className={order.id === selected ? "is-on" : ""}
                  aria-pressed={order.id === selected}
                  onClick={() => setSelected(order.id)}
                >
                  <strong>{titleOf(order.summary)}</strong>
                  <span>{when(order.created_at)}</span>
                </button>
              </li>
            ))}
          </ul>
          {current && (
            <article className="usage-order-detail" data-testid="order-detail">
              <h2>{titleOf(current.summary)}</h2>
              <dl>
                {fieldsOf(current).map((row) => (
                  <div key={row.label}>
                    <dt>{row.label}</dt>
                    <dd>{row.value || "—"}</dd>
                  </div>
                ))}
              </dl>
              <p className="muted">
                {when(current.created_at)} · Projeto {current.project_id}
              </p>
            </article>
          )}
        </div>
      )}
    </div>
  );
}
