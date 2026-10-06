import { FormEvent, useCallback, useEffect, useState } from "react";
import logo from "./assets/logo.png";
import { api } from "./api";
import { OwnerNav } from "./OwnerNav";
import type { OwnerUser } from "./types";
import "./usage.css";

const STORAGE_KEY = "storyrus.usage.password";

function when(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

const EMPTY: OwnerUser = {
  id: "",
  email: "",
  credits: 0,
  created_at: "",
  project_count: 0,
  full_name: "",
  phone: "",
  email_verified: false,
  postal_code: "",
  street: "",
  number: "",
  complement: "",
  district: "",
  city: "",
  state: "",
  country: "",
};

export function Usuarios() {
  const [password, setPassword] = useState(() => sessionStorage.getItem(STORAGE_KEY) ?? "");
  const [draft, setDraft] = useState("");
  const [users, setUsers] = useState<OwnerUser[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<OwnerUser | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

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
        setDetail(null);
        setSelectedId(null);
        setError("Senha inválida.");
      } else if (status === 429) {
        sessionStorage.removeItem(STORAGE_KEY);
        setPassword("");
        setUsers(null);
        setDetail(null);
        setSelectedId(null);
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

  async function openUser(id: string) {
    setSelectedId(id);
    setSaved(false);
    setError(null);
    try {
      setDetail(await api.user(password, id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao abrir o usuário.");
    }
  }

  function setField<K extends keyof OwnerUser>(key: K, value: OwnerUser[K]) {
    setDetail((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSaved(false);
  }

  async function saveUser(ev: FormEvent) {
    ev.preventDefault();
    if (!detail) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const next = await api.updateUser(password, detail.id, {
        email: detail.email.trim(),
        credits: Number(detail.credits) || 0,
        email_verified: Boolean(detail.email_verified),
        full_name: (detail.full_name ?? "").trim() || null,
        phone: (detail.phone ?? "").trim() || null,
        postal_code: (detail.postal_code ?? "").trim() || null,
        street: (detail.street ?? "").trim() || null,
        number: (detail.number ?? "").trim() || null,
        complement: (detail.complement ?? "").trim() || null,
        district: (detail.district ?? "").trim() || null,
        city: (detail.city ?? "").trim() || null,
        state: (detail.state ?? "").trim() || null,
        country: (detail.country ?? "").trim().toUpperCase() || null,
      });
      setDetail(next);
      setUsers((list) => list?.map((item) => (item.id === next.id ? { ...item, ...next } : item)) ?? null);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar o usuário.");
    } finally {
      setSaving(false);
    }
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

  const form = detail ?? EMPTY;

  return (
    <div className="usage usage-wide">
      <header className="usage-head">
        <img className="hdr-logo" src={logo} alt="Story R Us" />
        <div>
          <h1>Usuários</h1>
          <p className="muted">
            Contas cadastradas (sem convidados). {total} no total. Clique para ver e editar.
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
            setDetail(null);
            setSelectedId(null);
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
        <div className="usage-user-layout">
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
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {(users ?? []).map((user) => (
                    <tr key={user.id} className={selectedId === user.id ? "is-on" : undefined}>
                      <td>{user.full_name || "—"}</td>
                      <td>{user.email}</td>
                      <td>{user.phone || "—"}</td>
                      <td>{when(user.created_at)}</td>
                      <td>{user.email_verified ? "Sim" : "Não"}</td>
                      <td>{user.credits}</td>
                      <td>{user.project_count}</td>
                      <td>
                        <button
                          type="button"
                          className="usage-row-btn"
                          onClick={() => void openUser(user.id)}
                          data-testid={`owner-user-open-${user.id}`}
                        >
                          Ver / editar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="usage-panel usage-user-detail" data-testid="owner-user-detail">
            {selectedId && detail ? (
              <form onSubmit={(ev) => void saveUser(ev)}>
                <h2>Dados da conta</h2>
                <p className="muted">
                  Cadastro {when(detail.created_at)} · {detail.project_count} projeto
                  {detail.project_count === 1 ? "" : "s"}
                  {detail.terms_accepted_at ? ` · termos em ${when(detail.terms_accepted_at)}` : ""}
                </p>
                <div className="usage-user-form">
                  <label>
                    Nome
                    <input
                      value={form.full_name ?? ""}
                      onChange={(e) => setField("full_name", e.target.value)}
                      data-testid="owner-user-full-name"
                    />
                  </label>
                  <label>
                    E-mail
                    <input
                      type="email"
                      required
                      value={form.email}
                      onChange={(e) => setField("email", e.target.value)}
                      data-testid="owner-user-email"
                    />
                  </label>
                  <label>
                    Telefone
                    <input
                      value={form.phone ?? ""}
                      onChange={(e) => setField("phone", e.target.value)}
                      data-testid="owner-user-phone"
                    />
                  </label>
                  <label>
                    Créditos
                    <input
                      type="number"
                      min={0}
                      value={form.credits}
                      onChange={(e) => setField("credits", Number(e.target.value))}
                      data-testid="owner-user-credits"
                    />
                  </label>
                  <label className="usage-check">
                    <input
                      type="checkbox"
                      checked={Boolean(form.email_verified)}
                      onChange={(e) => setField("email_verified", e.target.checked)}
                      data-testid="owner-user-verified"
                    />
                    E-mail verificado
                  </label>
                  <label>
                    CEP / ZIP
                    <input
                      value={form.postal_code ?? ""}
                      onChange={(e) => setField("postal_code", e.target.value)}
                      data-testid="owner-user-postal"
                    />
                  </label>
                  <label className="usage-span-2">
                    Rua
                    <input
                      value={form.street ?? ""}
                      onChange={(e) => setField("street", e.target.value)}
                      data-testid="owner-user-street"
                    />
                  </label>
                  <label>
                    Número
                    <input
                      value={form.number ?? ""}
                      onChange={(e) => setField("number", e.target.value)}
                    />
                  </label>
                  <label>
                    Complemento
                    <input
                      value={form.complement ?? ""}
                      onChange={(e) => setField("complement", e.target.value)}
                    />
                  </label>
                  <label>
                    Bairro
                    <input
                      value={form.district ?? ""}
                      onChange={(e) => setField("district", e.target.value)}
                    />
                  </label>
                  <label>
                    Cidade
                    <input
                      value={form.city ?? ""}
                      onChange={(e) => setField("city", e.target.value)}
                      data-testid="owner-user-city"
                    />
                  </label>
                  <label>
                    Estado
                    <input
                      value={form.state ?? ""}
                      onChange={(e) => setField("state", e.target.value)}
                    />
                  </label>
                  <label>
                    País
                    <input
                      maxLength={2}
                      value={form.country ?? ""}
                      onChange={(e) => setField("country", e.target.value.toUpperCase())}
                    />
                  </label>
                </div>
                <div className="usage-user-actions">
                  <button type="submit" disabled={saving} data-testid="owner-user-save">
                    {saving ? "Salvando…" : "Salvar"}
                  </button>
                  <button
                    type="button"
                    className="link"
                    onClick={() => {
                      setSelectedId(null);
                      setDetail(null);
                      setSaved(false);
                    }}
                  >
                    Fechar
                  </button>
                  {saved && (
                    <span className="muted" data-testid="owner-user-saved">
                      Alterações salvas.
                    </span>
                  )}
                </div>
              </form>
            ) : (
              <p className="muted">Selecione um usuário para ver os dados e editar.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
