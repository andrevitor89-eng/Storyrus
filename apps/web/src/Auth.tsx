import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "./api";
import { SHARED, useLang, type Lang } from "./i18n";
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

type FieldErr = { field: string; message: string } | null;

function firstFieldError(form: HTMLFormElement, lang: Lang): FieldErr {
  const t = SHARED[lang];
  const fields = [...form.querySelectorAll("input")] as HTMLInputElement[];
  for (const el of fields) {
    if (el.disabled) continue;
    if (!el.value.trim()) return { field: el.name || el.id, message: t.required };
    if (el.type === "email" && el.validity.typeMismatch) {
      return { field: el.name || el.id, message: t.email_invalid };
    }
    if (el.validity.tooShort) {
      return { field: el.name || el.id, message: t.too_short.replace("{n}", String(el.minLength)) };
    }
  }
  return null;
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label>
      {label}
      {children}
      {error ? <span className="auth-field-error" role="alert">{error}</span> : null}
    </label>
  );
}

export function Login() {
  const [lang] = useLang();
  const t = AUTH[lang];
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErr, setFieldErr] = useState<FieldErr>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const next = firstFieldError(e.currentTarget, lang);
    setFieldErr(next);
    if (next) {
      const el = e.currentTarget.querySelector(`[name="${next.field}"]`) as HTMLInputElement | null;
      el?.focus();
      return;
    }
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
        <form className="auth-form" onSubmit={onSubmit} noValidate>
          <Field label={t.email} error={fieldErr?.field === "email" ? fieldErr.message : undefined}>
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(ev) => { setEmail(ev.target.value); setFieldErr(null); }}
              required
            />
          </Field>
          <Field label={t.password} error={fieldErr?.field === "password" ? fieldErr.message : undefined}>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(ev) => { setPassword(ev.target.value); setFieldErr(null); }}
              required
              minLength={8}
            />
          </Field>
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
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErr, setFieldErr] = useState<FieldErr>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const next = firstFieldError(e.currentTarget, lang);
    setFieldErr(next);
    if (next) {
      const el = e.currentTarget.querySelector(`[name="${next.field}"]`) as HTMLInputElement | null;
      el?.focus();
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
        <form className="auth-form" onSubmit={onSubmit} noValidate autoComplete="off">
          <Field label={t.name} error={fieldErr?.field === "fullName" ? fieldErr.message : undefined}>
            <input
              id="register-name"
              type="text"
              name="fullName"
              autoComplete="off"
              value={name}
              onChange={(ev) => { setName(ev.target.value); setFieldErr(null); }}
              required
              minLength={2}
              maxLength={80}
            />
          </Field>
          <Field label={t.email} error={fieldErr?.field === "email" ? fieldErr.message : undefined}>
            <input
              type="email"
              name="email"
              autoComplete="off"
              value={email}
              onChange={(ev) => { setEmail(ev.target.value); setFieldErr(null); }}
              required
            />
          </Field>
          <Field label={t.password} error={fieldErr?.field === "password" ? fieldErr.message : undefined}>
            <input
              type="password"
              name="password"
              autoComplete="new-password"
              value={password}
              onChange={(ev) => { setPassword(ev.target.value); setFieldErr(null); }}
              required
              minLength={8}
            />
          </Field>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="kbtn kbtn-primary auth-cta" type="submit" disabled={busy}>
            {busy ? t.register_busy : t.register_cta}
          </button>
        </form>
      </AuthCard>
    </SimpleShell>
  );
}
