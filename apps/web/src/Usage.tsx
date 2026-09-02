import { FormEvent, useCallback, useEffect, useState } from "react";
import logo from "./assets/logo.png";
import { api } from "./api";
import type { UsageReport } from "./types";
import "./usage.css";

const STORAGE_KEY = "storyrus.usage.password";
const STEP_LABEL: Record<string, string> = {
  AVATAR: "Personagem",
  REALISTIC: "Retrato",
  STORY: "História",
  EBOOK: "E-book",
  STORYBOARD: "Roteiro",
  VIDEO: "Vídeo",
  EXTRA_CHARACTER: "Personagem extra",
};

function money(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

function when(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

export function Usage() {
  const [password, setPassword] = useState(() => sessionStorage.getItem(STORAGE_KEY) ?? "");
  const [draft, setDraft] = useState("");
  const [data, setData] = useState<UsageReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (secret: string) => {
    setLoading(true);
    setError(null);
    try {
      const report = await api.usage(secret);
      setData(report);
      sessionStorage.setItem(STORAGE_KEY, secret);
      setPassword(secret);
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      if (status === 401) {
        sessionStorage.removeItem(STORAGE_KEY);
        setPassword("");
        setData(null);
        setError("Senha inválida.");
      } else if (status === 503) {
        setError("Painel ainda não configurado no servidor.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao carregar gastos.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (password) void load(password);
  }, [password, load]);

  useEffect(() => {
    if (!password) return;
    const id = window.setInterval(() => void load(password), 20_000);
    return () => window.clearInterval(id);
  }, [password, load]);

  function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    const next = draft.trim();
    if (next) void load(next);
  }

  if (!password || (error && !data)) {
    return (
      <div className="usage">
        <div className="usage-gate card auth">
          <img className="auth-logo" src={logo} alt="Story R Us" />
          <h1>Gastos da plataforma</h1>
          <p className="muted">Página privada. Digite a senha combinada.</p>
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
          <h1>Gastos da plataforma</h1>
          <p className="muted">Atualiza a cada 20s · fuso de Brasília</p>
        </div>
        <button
          className="link"
          type="button"
          onClick={() => {
            sessionStorage.removeItem(STORAGE_KEY);
            setPassword("");
            setData(null);
            setDraft("");
          }}
        >
          Sair
        </button>
      </header>

      {error && <p className="error">{error}</p>}

      <section className="usage-cards">
        <article>
          <span>Hoje</span>
          <strong>{money(data?.today_usd)}</strong>
        </article>
        <article>
          <span>Mês</span>
          <strong>{money(data?.month_usd)}</strong>
        </article>
        <article>
          <span>Ticket médio / livro</span>
          <strong>{money(data?.avg_book_usd)}</strong>
        </article>
      </section>

      <section className="usage-panel">
        <h2>Por etapa</h2>
        {data?.by_type.length ? (
          <ul className="usage-bars">
            {data.by_type.map((b) => (
              <li key={b.key}>
                <span>{STEP_LABEL[b.key] ?? b.key}</span>
                <em>{money(b.usd)}</em>
                <small>{b.jobs} job{b.jobs === 1 ? "" : "s"}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Nenhum custo medido neste mês ainda.</p>
        )}
      </section>

      <section className="usage-panel">
        <h2>Livros do período</h2>
        <div className="usage-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Criança</th>
                <th>Status</th>
                <th>USD</th>
                <th>Atualizado</th>
              </tr>
            </thead>
            <tbody>
              {(data?.books ?? []).map((book) => (
                <tr key={book.project_id}>
                  <td>{book.child_name || "Sem nome"}</td>
                  <td>{book.status}</td>
                  <td>
                    {money(book.usd)}
                    {book.unmeasured_jobs > 0 && (
                      <small className="muted"> · {book.unmeasured_jobs} sem medição</small>
                    )}
                  </td>
                  <td>{when(book.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.books.length && <p className="muted">Nenhum livro no período.</p>}
        </div>
      </section>
    </div>
  );
}
