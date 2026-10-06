import { FormEvent, useCallback, useEffect, useState } from "react";
import logo from "./assets/logo.png";
import { api, getToken } from "./api";
import { OwnerNav } from "./OwnerNav";
import {
  OWNER_SESSION_TOKEN,
  apiOwnerPassword,
  canTryOwnerSession,
  clearOwnerSecret,
  ownerGateError,
  persistOwnerSecret,
  readOwnerSecret,
} from "./ownerSession";
import { useOwnerPageTitle } from "./useOwnerPageTitle";
import type { OrderTicket } from "./types";
import "./usage.css";

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
      value: order.cover_type === "soft" ? "Capa flexível" : "Capa dura",
    });
  }
  if (order.style) {
    rows.push({
      label: "Estilo",
      value: order.style === "cartoon" ? "Cartoon" : "Realista",
    });
  }
  if (order.print_code) rows.push({ label: "Código do impresso", value: order.print_code });
  if (order.print_status) {
    const labels: Record<string, string> = {
      awaiting_spec: "Aguardando especificação",
      awaiting_pages: "Aguardando páginas",
      held: "Formato ainda não liberado",
      files_ready: "Arquivos prontos",
      sent_for_validation: "Enviado para validação",
      approved: "Aprovado",
      rejected: "Recusado",
    };
    rows.push({ label: "Produção", value: labels[order.print_status] ?? order.print_status });
  }
  if (order.payment_status) rows.push({ label: "Pagamento", value: order.payment_status });
  if (order.tracking_code) rows.push({ label: "Rastreio", value: order.tracking_code });
  return rows;
}

export function Pedidos() {
  useOwnerPageTitle("/pedidos");
  const [password, setPassword] = useState(() => readOwnerSecret());
  const [draft, setDraft] = useState("");
  const [orders, setOrders] = useState<OrderTicket[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionTried, setSessionTried] = useState(false);

  const load = useCallback(async (secret: string) => {
    setLoading(true);
    setError(null);
    try {
      const report = await api.usage(apiOwnerPassword(secret));
      const list = report.orders ?? [];
      setOrders(list);
      setSelected((cur) => (cur && list.some((order) => order.id === cur) ? cur : list[0]?.id ?? null));
      const next = apiOwnerPassword(secret) ? secret.trim() : OWNER_SESSION_TOKEN;
      persistOwnerSecret(next);
      setPassword(next);
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      if (status === 401 || status === 429) {
        clearOwnerSecret();
        setPassword("");
        setOrders(null);
      }
      setError(ownerGateError(status, err instanceof Error ? err.message : "Falha ao carregar pedidos."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (password) {
      void load(password);
      return;
    }
    if (!sessionTried && canTryOwnerSession()) {
      setSessionTried(true);
      void load(OWNER_SESSION_TOKEN);
    }
  }, [password, load, sessionTried]);

  function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    const next = draft.trim();
    if (next) void load(next);
  }

  const current = orders?.find((order) => order.id === selected) ?? null;
  const ownerSecret = apiOwnerPassword(password);

  if (!password || (error && !orders)) {
    return (
      <div className="usage">
        <div className="usage-gate card auth">
          <img className="auth-logo" src={logo} alt="Story R Us" />
          <h1>Pedidos</h1>
          <p className="muted">
            Página restrita a contas administradoras. Com a conta admin logada o painel abre sozinho.
            A senha compartilhada só vale se o servidor ainda estiver com o fallback ligado.
          </p>
          {getToken() && loading && <p className="muted">Abrindo com a sessão do estúdio…</p>}
          <form onSubmit={onSubmit}>
            <label>
              Senha do painel
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
        <OwnerNav current="pedidos" />
        <button
          className="link"
          type="button"
          onClick={() => {
            clearOwnerSecret();
            setPassword("");
            setOrders(null);
            setDraft("");
            setSessionTried(true);
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
              {(current.photo_urls ?? []).length > 0 && (
                <div className="usage-order-photos">
                  {(current.photo_urls ?? []).map((url) => (
                    <figure key={url}>
                      <img src={url} alt="Foto enviada no pedido" />
                      <a href={url} target="_blank" rel="noreferrer">
                        Abrir imagem
                      </a>
                    </figure>
                  ))}
                </div>
              )}
              <p className="muted">
                {when(current.created_at)} · Projeto {current.project_id}
              </p>
              {current.print_order_id && current.print_status === "files_ready" && (
                <button
                  type="button"
                  onClick={() =>
                    void api
                      .setPrintValidation(ownerSecret, current.print_order_id as string, "sent_for_validation")
                      .then(() => load(password))
                      .catch((err: Error) => setError(err.message))
                  }
                >
                  Enviar para validação
                </button>
              )}
              {current.print_order_id && current.print_status === "sent_for_validation" && (
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    type="button"
                    onClick={() =>
                      void api
                        .setPrintValidation(ownerSecret, current.print_order_id as string, "approved")
                        .then(() => load(password))
                        .catch((err: Error) => setError(err.message))
                    }
                  >
                    Aprovar produção
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      void api
                        .setPrintValidation(ownerSecret, current.print_order_id as string, "rejected")
                        .then(() => load(password))
                        .catch((err: Error) => setError(err.message))
                    }
                  >
                    Recusar produção
                  </button>
                </div>
              )}
              {current.print_order_id &&
                ["files_ready", "sent_for_validation", "approved", "rejected"].includes(
                  current.print_status ?? "",
                ) && (
                  <button
                    type="button"
                    onClick={() =>
                      void api.downloadPrintPackage(ownerSecret, current.print_order_id as string).then((blob) => {
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = `${current.print_code ?? "impresso"}.zip`;
                        link.click();
                        URL.revokeObjectURL(url);
                      })
                    }
                  >
                    Baixar pacote
                  </button>
                )}
            </article>
          )}
        </div>
      )}
    </div>
  );
}
