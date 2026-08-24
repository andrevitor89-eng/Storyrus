import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "./api";
import { SHARED, useLang, validityHandlers } from "./i18n";
import { SimpleShell } from "./SiteChrome";

const AUTH = {
  pt: {
    login_title: "Entrar",
    login_lead: "Continue a história em que seu filho é o herói.",
    login_cta: "Entrar",
    login_busy: "Entrando...",
    register_title: "Criar conta",
    register_lead: "Comece a transformar fotos em livros e vídeos.",
    register_cta: "Começar",
    register_busy: "Criando...",
    name: "Seu nome",
    email: "E-mail",
    password: "Senha",
    has_account: "Já tem conta?",
    no_account: "Não tem conta?",
    signup_link: "Cadastre-se",
  },
  en: {
    login_title: "Log in",
    login_lead: "Continue the story where your child is the hero.",
    login_cta: "Log in",
    login_busy: "Signing in...",
    register_title: "Create account",
    register_lead: "Start turning photos into books and videos.",
    register_cta: "Get started",
    register_busy: "Creating...",
    name: "Your name",
    email: "Email",
    password: "Password",
    has_account: "Already have an account?",
    no_account: "No account yet?",
    signup_link: "Sign up",
  },
} as const;

function AuthCard({
  title,
  lead,
  children,
  foot,
}: {
  title: string;
  lead: string;
  children: React.ReactNode;
  foot: React.ReactNode;
}) {
  return (
    <section className="auth-card">
      <h1>{title}</h1>
      <p className="auth-lead">{lead}</p>
      {children}
      <p className="auth-foot">{foot}</p>
    </section>
  );
}

export function Login() {
  const [lang] = useLang();
  const t = AUTH[lang];
  const v = validityHandlers(lang);
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const out = await api.login(email.trim(), password);
      setToken(out.access_token);
      nav("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <SimpleShell>
      <AuthCard
        title={t.login_title}
        lead={t.login_lead}
        foot={<>{t.no_account} <Link to="/register">{t.signup_link}</Link></>}
      >
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            {t.email}
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              required
              {...v}
            />
          </label>
          <label>
            {t.password}
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(ev) => setPassword(ev.target.value)}
              required
              minLength={8}
              {...v}
            />
          </label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="kbtn kbtn-primary auth-cta" type="submit" disabled={busy}>
            {busy ? t.login_busy : t.login_cta}
          </button>
        </form>
      </AuthCard>
    </SimpleShell>
  );
}

export function Register() {
  const [lang] = useLang();
  const t = AUTH[lang];
  const v = validityHandlers(lang);
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const nameEl = e.currentTarget.elements.namedItem("name") as HTMLInputElement;
    if (!nameEl.value.trim()) {
      nameEl.setCustomValidity(SHARED[lang].required);
      nameEl.reportValidity();
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const out = await api.register(email.trim(), password, name.trim());
      setToken(out.access_token);
      nav("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <SimpleShell>
      <AuthCard
        title={t.register_title}
        lead={t.register_lead}
        foot={<>{t.has_account} <Link to="/login">{SHARED[lang].login}</Link></>}
      >
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            {t.name}
            <input
              name="name"
              autoComplete="name"
              value={name}
              onChange={(ev) => setName(ev.target.value)}
              required
              minLength={2}
              maxLength={80}
              {...v}
            />
          </label>
          <label>
            {t.email}
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              required
              {...v}
            />
          </label>
          <label>
            {t.password}
            <input
              type="password"
              name="password"
              autoComplete="new-password"
              value={password}
              onChange={(ev) => setPassword(ev.target.value)}
              required
              minLength={8}
              {...v}
            />
          </label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="kbtn kbtn-primary auth-cta" type="submit" disabled={busy}>
            {busy ? t.register_busy : t.register_cta}
          </button>
        </form>
      </AuthCard>
    </SimpleShell>
  );
}
