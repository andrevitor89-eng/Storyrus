import { FormEvent, useCallback, useEffect, useState } from "react";
import logo from "./assets/logo.png";
import { api } from "./api";
import { OwnerNav } from "./OwnerNav";
import type { OwnerUser } from "./types";
import "./usage.css";

const STORAGE_KEY = "storyrus.usage.password";

function when(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

export function Usuarios() {
  const [password, setPassword] = useState(() => sessionStorage.getItem(STORAGE_KEY) ?? "");
  const [draft, setDraft] = useState("");
  const [users, setUsers] = useState<OwnerUser[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (secret: string) => {
    setLoading(true);
    setError(null);
    try {
      const report = await api.users(secret);
      setUsers(report.users);
      setTotal(report.total);
      sessionStorage.setItem(STORAGE_KEY, secret);
      setPassword(secret);
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      if (status === 401) {
        sessionStorage.removeItem(STORAGE_KEY);
        setPassword("");
        setUsers(null);
        setError("Senha inválida.");
      } else if (status === 429) {
        sessionStorage.removeItem(STORAGE_KEY);
        setPassword("");
        setUsers(null);
        setError("Muitas tentativas. Aguarde e tente de novo.");
      } else if (status === 503) {
        setError("Painel ainda não configurado no servidor.");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao carregar usuários.");
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

  if (!password || (error && !users)) {
    return (
      <div className="usage">
        <div className="usage-gate card auth">
          <img className="auth-logo" src={logo} alt="Story R Us" />
          <h1>Usuários</h1>
          <p className="muted">Página privada do dono. Use a mesma senha de Gastos e Pedidos.</p>
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
          <h1>Usuários</h1>
          <p className="muted">
            Contas cadastradas (sem convidados). {total} no total.
          </p>
        </div>
        <OwnerNav current="usuarios" />
        <button
          className="link"
          type="button"
          onClick={() => {
            sessionStorage.removeItem(STORAGE_KEY);
            setPassword("");
            setUsers(null);
            setDraft("");
          }}
        >
          Sair
        </button>
      </header>

      {error && <p className="error">{error}</p>}

      {(users ?? []).length === 0 ? (
        <p className="muted">Nenhuma conta cadastrada ainda.</p>
      ) : (
        <section className="usage-panel">
          <div className="usage-table-wrap">
            <table aria-label="Lista de usuários">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>E-mail</th>
                  <th>Telefone</th>
                  <th>Cadastro</th>
                  <th>Verificado</th>
                  <th>Créditos</th>
                  <th>Projetos</th>
                </tr>
              </thead>
              <tbody>
                {(users ?? []).map((user) => (
                  <tr key={user.id}>
                    <td>{user.full_name || "—"}</td>
                    <td>{user.email}</td>
                    <td>{user.phone || "—"}</td>
                    <td>{when(user.created_at)}</td>
                    <td>{user.email_verified ? "Sim" : "Não"}</td>
                    <td>{user.credits}</td>
                    <td>{user.project_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
