import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import logo from "./assets/logo.png";
import { api } from "./api";
import "./landing.css";

export type AuthMode = "login" | "signup";

type Lang = "pt" | "en" | "es";

const COPY: Record<
  Lang,
  {
    loginTitle: string;
    signupTitle: string;
    loginLead: string;
    signupLead: string;
    email: string;
    password: string;
    loginSubmit: string;
    signupSubmit: string;
    busy: string;
    switchToSignup: string;
    switchToLogin: string;
    back: string;
  }
> = {
  pt: {
    loginTitle: "Entrar",
    signupTitle: "Criar conta",
    loginLead: "Acesse sua conta para criar livros personalizados.",
    signupLead: "Cadastre-se para criar livros personalizados.",
    email: "E-mail",
    password: "Senha (mín. 8)",
    loginSubmit: "Entrar",
    signupSubmit: "Criar conta",
    busy: "Aguarde…",
    switchToSignup: "Criar uma conta",
    switchToLogin: "Já tenho conta",
    back: "Voltar ao início",
  },
  en: {
    loginTitle: "Log in",
    signupTitle: "Create account",
    loginLead: "Sign in to create personalized books.",
    signupLead: "Create an account to make personalized books.",
    email: "Email",
    password: "Password (min. 8)",
    loginSubmit: "Log in",
    signupSubmit: "Create account",
    busy: "Please wait…",
    switchToSignup: "Create an account",
    switchToLogin: "I already have an account",
    back: "Back to home",
  },
  es: {
    loginTitle: "Entrar",
    signupTitle: "Crear cuenta",
    loginLead: "Accede a tu cuenta para crear libros personalizados.",
    signupLead: "Regístrate para crear libros personalizados.",
    email: "Correo",
    password: "Contraseña (mín. 8)",
    loginSubmit: "Entrar",
    signupSubmit: "Crear cuenta",
    busy: "Espera…",
    switchToSignup: "Crear una cuenta",
    switchToLogin: "Ya tengo cuenta",
    back: "Volver al inicio",
  },
};

function readLang(): Lang {
  try {
    const s = localStorage.getItem("lang");
    if (s === "en" || s === "es" || s === "pt") return s;
  } catch {
    /* ignore */
  }
  return "pt";
}

/** Evita open-redirect: só caminhos relativos internos. */
export function safeNextPath(raw: string | null | undefined): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/app";
  return raw;
}

/** Encaminha para o cadastro preservando o destino do estúdio. */
export function accountGateHref(nextPath: string): string {
  const next = safeNextPath(nextPath);
  return `/cadastro?next=${encodeURIComponent(next)}`;
}

export function Auth({ mode }: { mode: AuthMode }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = useMemo(() => safeNextPath(params.get("next")), [params]);
  const t = COPY[readLang()];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const altMode: AuthMode = mode === "login" ? "signup" : "login";
  const altPath = altMode === "login" ? "/entrar" : "/cadastro";
  const altHref = `${altPath}?next=${encodeURIComponent(next)}`;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "signup") await api.signup(email.trim(), password);
      else await api.login(email.trim(), password);
      navigate(next, { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="kid auth-kid" data-testid="auth-page">
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-logo">
            <Link to="/">
              <img src={logo} alt="Story R Us" />
            </Link>
          </div>
          <h1>{mode === "login" ? t.loginTitle : t.signupTitle}</h1>
          <p className="auth-lead">{mode === "login" ? t.loginLead : t.signupLead}</p>
          <form className="auth-form" onSubmit={onSubmit} data-testid="auth-form">
            <label>
              {t.email}
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                data-testid="auth-email"
              />
            </label>
            <label>
              {t.password}
              <input
                type="password"
                required
                minLength={8}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                data-testid="auth-password"
              />
            </label>
            {error && (
              <p className="auth-error" role="alert" data-testid="auth-error">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="kbtn kbtn-primary auth-cta"
              disabled={busy}
              data-testid="auth-submit"
            >
              {busy ? t.busy : mode === "login" ? t.loginSubmit : t.signupSubmit}
            </button>
          </form>
          <p className="auth-foot">
            <Link to={altHref} data-testid="auth-switch">
              {mode === "login" ? t.switchToSignup : t.switchToLogin}
            </Link>
          </p>
          <p className="auth-foot">
            <Link to="/" data-testid="auth-back">
              {t.back}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
