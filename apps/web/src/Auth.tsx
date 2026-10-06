import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import logo from "./assets/logo.png";
import { api, getToken, type SignupPayload } from "./api";
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
    passwordConfirm: string;
    fullName: string;
    phone: string;
    country: string;
    postalCode: string;
    postalCodeBr: string;
    street: string;
    number: string;
    complement: string;
    district: string;
    districtOptional: string;
    city: string;
    state: string;
    stateBr: string;
    acceptTerms: string;
    terms: string;
    privacy: string;
    loginSubmit: string;
    signupSubmit: string;
    busy: string;
    switchToSignup: string;
    switchToLogin: string;
    forgotPassword: string;
    back: string;
    checkTitle: string;
    checkLead: string;
    checkHint: string;
    passwordMismatch: string;
    mustAcceptTerms: string;
    resend: string;
    resendBusy: string;
    resendOk: string;
  }
> = {
  pt: {
    loginTitle: "Entrar",
    signupTitle: "Criar conta",
    loginLead: "Acesse sua conta para criar livros personalizados.",
    signupLead: "Cadastre-se com seus dados — usamos o perfil no pedido e no envio (Brasil e exterior).",
    email: "E-mail",
    password: "Senha (mín. 8)",
    passwordConfirm: "Confirmar senha",
    fullName: "Nome completo",
    phone: "Telefone / WhatsApp",
    country: "País",
    postalCode: "Código postal",
    postalCodeBr: "CEP",
    street: "Rua / endereço",
    number: "Número",
    complement: "Complemento",
    district: "Bairro",
    districtOptional: "Bairro / distrito (opcional)",
    city: "Cidade",
    state: "Estado / região",
    stateBr: "UF",
    acceptTerms: "Li e aceito os",
    terms: "Termos de uso",
    privacy: "Política de privacidade",
    loginSubmit: "Entrar",
    signupSubmit: "Criar conta",
    busy: "Aguarde…",
    switchToSignup: "Criar uma conta",
    switchToLogin: "Já tenho conta",
    forgotPassword: "Esqueci a senha",
    back: "Voltar ao início",
    checkTitle: "Verifique seu e-mail",
    checkLead: "Enviamos um link de confirmação. Ative a conta antes de entrar no estúdio.",
    checkHint: "Não recebeu? Confira o spam ou tente criar a conta de novo em alguns minutos.",
    passwordMismatch: "As senhas não coincidem.",
    mustAcceptTerms: "Aceite os termos e a política de privacidade.",
    resend: "Reenviar e-mail de confirmação",
    resendBusy: "Enviando…",
    resendOk: "Se a conta estiver pendente, enviamos um novo link.",
  },
  en: {
    loginTitle: "Log in",
    signupTitle: "Create account",
    loginLead: "Sign in to create personalized books.",
    signupLead: "Sign up with your details — we reuse them for orders and shipping (Brazil and abroad).",
    email: "Email",
    password: "Password (min. 8)",
    passwordConfirm: "Confirm password",
    fullName: "Full name",
    phone: "Phone / WhatsApp",
    country: "Country",
    postalCode: "Postal / ZIP code",
    postalCodeBr: "CEP (Brazil)",
    street: "Street address",
    number: "Number",
    complement: "Apt / Suite",
    district: "District",
    districtOptional: "District / neighborhood (optional)",
    city: "City",
    state: "State / region",
    stateBr: "State (UF)",
    acceptTerms: "I agree to the",
    terms: "Terms of use",
    privacy: "Privacy policy",
    loginSubmit: "Log in",
    signupSubmit: "Create account",
    busy: "Please wait…",
    switchToSignup: "Create an account",
    switchToLogin: "I already have an account",
    forgotPassword: "Forgot password",
    back: "Back to home",
    checkTitle: "Check your email",
    checkLead: "We sent a confirmation link. Activate your account before opening the studio.",
    checkHint: "Didn't get it? Check spam or try signing up again in a few minutes.",
    passwordMismatch: "Passwords do not match.",
    mustAcceptTerms: "Please accept the terms and privacy policy.",
    resend: "Resend confirmation email",
    resendBusy: "Sending…",
    resendOk: "If the account is still pending, we sent a new link.",
  },
  es: {
    loginTitle: "Entrar",
    signupTitle: "Crear cuenta",
    loginLead: "Accede a tu cuenta para crear libros personalizados.",
    signupLead: "Regístrate con tus datos — los usamos en el pedido y el envío (Brasil y el exterior).",
    email: "Correo",
    password: "Contraseña (mín. 8)",
    passwordConfirm: "Confirmar contraseña",
    fullName: "Nombre completo",
    phone: "Teléfono / WhatsApp",
    country: "País",
    postalCode: "Código postal",
    postalCodeBr: "CEP (Brasil)",
    street: "Calle / dirección",
    number: "Número",
    complement: "Complemento",
    district: "Barrio",
    districtOptional: "Barrio / distrito (opcional)",
    city: "Ciudad",
    state: "Estado / región",
    stateBr: "UF",
    acceptTerms: "Acepto los",
    terms: "Términos de uso",
    privacy: "Política de privacidad",
    loginSubmit: "Entrar",
    signupSubmit: "Crear cuenta",
    busy: "Espera…",
    switchToSignup: "Crear una cuenta",
    switchToLogin: "Ya tengo cuenta",
    forgotPassword: "Olvidé la contraseña",
    back: "Volver al inicio",
    checkTitle: "Revisa tu correo",
    checkLead: "Enviamos un enlace de confirmación. Activa la cuenta antes de entrar al estudio.",
    checkHint: "¿No llegó? Revisa spam o vuelve a registrarte en unos minutos.",
    passwordMismatch: "Las contraseñas no coinciden.",
    mustAcceptTerms: "Acepta los términos y la política de privacidad.",
    resend: "Reenviar correo de confirmación",
    resendBusy: "Enviando…",
    resendOk: "Si la cuenta está pendiente, enviamos un enlace nuevo.",
  },
};

/** Países mais comuns no cadastro (ISO 3166-1 alpha-2). */
const COUNTRY_OPTIONS: { code: string; label: Record<Lang, string> }[] = [
  { code: "BR", label: { pt: "Brasil", en: "Brazil", es: "Brasil" } },
  { code: "US", label: { pt: "Estados Unidos", en: "United States", es: "Estados Unidos" } },
  { code: "PT", label: { pt: "Portugal", en: "Portugal", es: "Portugal" } },
  { code: "ES", label: { pt: "Espanha", en: "Spain", es: "España" } },
  { code: "AR", label: { pt: "Argentina", en: "Argentina", es: "Argentina" } },
  { code: "MX", label: { pt: "México", en: "Mexico", es: "México" } },
  { code: "CL", label: { pt: "Chile", en: "Chile", es: "Chile" } },
  { code: "CO", label: { pt: "Colômbia", en: "Colombia", es: "Colombia" } },
  { code: "UY", label: { pt: "Uruguai", en: "Uruguay", es: "Uruguay" } },
  { code: "PE", label: { pt: "Peru", en: "Peru", es: "Perú" } },
  { code: "CA", label: { pt: "Canadá", en: "Canada", es: "Canadá" } },
  { code: "GB", label: { pt: "Reino Unido", en: "United Kingdom", es: "Reino Unido" } },
  { code: "DE", label: { pt: "Alemanha", en: "Germany", es: "Alemania" } },
  { code: "FR", label: { pt: "França", en: "France", es: "Francia" } },
  { code: "IT", label: { pt: "Itália", en: "Italy", es: "Italia" } },
  { code: "AO", label: { pt: "Angola", en: "Angola", es: "Angola" } },
  { code: "MZ", label: { pt: "Moçambique", en: "Mozambique", es: "Mozambique" } },
  { code: "JP", label: { pt: "Japão", en: "Japan", es: "Japón" } },
  { code: "AU", label: { pt: "Austrália", en: "Australia", es: "Australia" } },
  { code: "NZ", label: { pt: "Nova Zelândia", en: "New Zealand", es: "Nueva Zelanda" } },
  { code: "IE", label: { pt: "Irlanda", en: "Ireland", es: "Irlanda" } },
  { code: "CH", label: { pt: "Suíça", en: "Switzerland", es: "Suiza" } },
  { code: "NL", label: { pt: "Países Baixos", en: "Netherlands", es: "Países Bajos" } },
  { code: "BE", label: { pt: "Bélgica", en: "Belgium", es: "Bélgica" } },
  { code: "SE", label: { pt: "Suécia", en: "Sweden", es: "Suecia" } },
  { code: "NO", label: { pt: "Noruega", en: "Norway", es: "Noruega" } },
  { code: "DK", label: { pt: "Dinamarca", en: "Denmark", es: "Dinamarca" } },
  { code: "FI", label: { pt: "Finlândia", en: "Finland", es: "Finlandia" } },
  { code: "PL", label: { pt: "Polônia", en: "Poland", es: "Polonia" } },
  { code: "AE", label: { pt: "Emirados Árabes", en: "United Arab Emirates", es: "Emiratos Árabes" } },
  { code: "IL", label: { pt: "Israel", en: "Israel", es: "Israel" } },
  { code: "IN", label: { pt: "Índia", en: "India", es: "India" } },
  { code: "CN", label: { pt: "China", en: "China", es: "China" } },
  { code: "KR", label: { pt: "Coreia do Sul", en: "South Korea", es: "Corea del Sur" } },
  { code: "SG", label: { pt: "Singapura", en: "Singapore", es: "Singapur" } },
  { code: "ZA", label: { pt: "África do Sul", en: "South Africa", es: "Sudáfrica" } },
];

function defaultCountry(lang: Lang): string {
  if (lang === "en") return "US";
  if (lang === "es") return "ES";
  return "BR";
}

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

/** Com sessão local, abre o estúdio; sem token, pede cadastro. */
export function studioEntryHref(nextPath: string): string {
  const next = safeNextPath(nextPath);
  if (getToken()) return next;
  return accountGateHref(next);
}

const emptySignup = {
  full_name: "",
  phone: "",
  country: defaultCountry(readLang()),
  postal_code: "",
  street: "",
  number: "",
  complement: "",
  district: "",
  city: "",
  state: "",
  password_confirm: "",
  accept_terms: false,
};

export function Auth({ mode }: { mode: AuthMode }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = useMemo(() => safeNextPath(params.get("next")), [params]);
  const t = COPY[readLang()];
  const lang = readLang();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signup, setSignup] = useState(emptySignup);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [checkEmail, setCheckEmail] = useState(false);
  const [resendHint, setResendHint] = useState<string | null>(null);

  const isBrazil = signup.country === "BR";
  const postalLabel = isBrazil ? t.postalCodeBr : t.postalCode;
  const stateLabel = isBrazil ? t.stateBr : t.state;
  const districtLabel = isBrazil ? t.district : t.districtOptional;

  const altMode: AuthMode = mode === "login" ? "signup" : "login";
  const altPath = altMode === "login" ? "/entrar" : "/cadastro";
  const altHref = `${altPath}?next=${encodeURIComponent(next)}`;

  function friendlyAuthError(raw: string): string {
    const msg = raw.trim();
    if (
      /^502\b|^503\b|^504\b/i.test(msg) ||
      /failed to fetch|networkerror|load failed|demorou demais|abort/i.test(msg)
    ) {
      return mode === "signup"
        ? "Não foi possível criar a conta agora. O servidor está indisponível — tente de novo em instantes."
        : "Não foi possível entrar agora. O servidor está indisponível — tente de novo em instantes.";
    }
    if (/^409\b/i.test(msg)) {
      return "Este e-mail já tem conta. Tente entrar.";
    }
    if (/^403\b/i.test(msg) || /confirme seu e-mail|verify|verif/i.test(msg)) {
      return "Confirme seu e-mail pelo link que enviamos antes de entrar.";
    }
    if (/^401\b/i.test(msg) || /credencial|senha|password|unauthorized/i.test(msg)) {
      return "E-mail ou senha incorretos.";
    }
    const cleaned = msg.replace(/^\d{3}:\s*/i, "").trim();
    return cleaned || msg || "Algo deu errado. Tente novamente.";
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "signup") {
        if (password !== signup.password_confirm) {
          setError(t.passwordMismatch);
          return;
        }
        if (!signup.accept_terms) {
          setError(t.mustAcceptTerms);
          return;
        }
        const payload: SignupPayload = {
          email: email.trim(),
          password,
          password_confirm: signup.password_confirm,
          full_name: signup.full_name.trim(),
          phone: signup.phone.trim(),
          postal_code: signup.postal_code.trim(),
          street: signup.street.trim(),
          number: signup.number.trim(),
          complement: signup.complement.trim() || null,
          district: signup.district.trim() || null,
          city: signup.city.trim(),
          state: signup.state.trim(),
          country: signup.country.trim().toUpperCase(),
          accept_terms: true,
        };
        await api.signup(payload);
        setCheckEmail(true);
        return;
      }
      await api.login(email.trim(), password);
      navigate(next, { replace: true });
    } catch (err) {
      const raw = (err as Error).message || "";
      if (mode === "login" && (/^403\b/i.test(raw) || /confirme seu e-mail|verify|verif/i.test(raw))) {
        setCheckEmail(true);
        return;
      }
      setError(friendlyAuthError(raw));
    } finally {
      setBusy(false);
    }
  }

  async function onResend() {
    const dest = email.trim();
    if (!dest) return;
    setBusy(true);
    setResendHint(null);
    try {
      await api.resendVerify(dest);
      setResendHint(t.resendOk);
    } catch {
      setResendHint(t.resendOk);
    } finally {
      setBusy(false);
    }
  }

  if (checkEmail) {
    return (
      <div className="kid auth-kid" data-testid="auth-page">
        <div className="auth-shell">
          <div className="auth-card" data-testid="auth-check-email">
            <div className="auth-logo">
              <Link to="/">
                <img src={logo} alt="Story R Us" />
              </Link>
            </div>
            <h1>{t.checkTitle}</h1>
            <p className="auth-lead">{t.checkLead}</p>
            <p className="auth-lead auth-check-hint">{t.checkHint}</p>
            {resendHint && (
              <p className="auth-lead auth-check-hint" data-testid="auth-resend-hint">
                {resendHint}
              </p>
            )}
            <p className="auth-foot">
              <button
                type="button"
                disabled={busy || !email.trim()}
                onClick={() => void onResend()}
                data-testid="auth-resend-verify"
              >
                {busy ? t.resendBusy : t.resend}
              </button>
            </p>
            <p className="auth-foot">
              <Link to={`/entrar?next=${encodeURIComponent(next)}`} data-testid="auth-switch">
                {t.switchToLogin}
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
            {mode === "signup" && (
              <label>
                {t.fullName}
                <input
                  type="text"
                  required
                  autoComplete="name"
                  value={signup.full_name}
                  onChange={(e) => setSignup({ ...signup, full_name: e.target.value })}
                  data-testid="auth-full-name"
                />
              </label>
            )}
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
            {mode === "signup" && (
              <label>
                {t.phone}
                <input
                  type="tel"
                  required
                  minLength={8}
                  autoComplete="tel"
                  value={signup.phone}
                  onChange={(e) => setSignup({ ...signup, phone: e.target.value })}
                  data-testid="auth-phone"
                />
              </label>
            )}
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
            {mode === "signup" && (
              <>
                <label>
                  {t.passwordConfirm}
                  <input
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={signup.password_confirm}
                    onChange={(e) => setSignup({ ...signup, password_confirm: e.target.value })}
                    data-testid="auth-password-confirm"
                  />
                </label>
                <div className="auth-address" data-testid="auth-address">
                  <label className="auth-span-2">
                    {t.country}
                    <select
                      required
                      value={signup.country}
                      onChange={(e) => setSignup({ ...signup, country: e.target.value })}
                      data-testid="auth-country"
                      autoComplete="country"
                    >
                      {COUNTRY_OPTIONS.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.label[lang]}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    {postalLabel}
                    <input
                      type="text"
                      required
                      minLength={2}
                      maxLength={16}
                      autoComplete="postal-code"
                      value={signup.postal_code}
                      onChange={(e) => setSignup({ ...signup, postal_code: e.target.value })}
                      data-testid="auth-postal-code"
                    />
                  </label>
                  <label className="auth-span-2">
                    {t.street}
                    <input
                      type="text"
                      required
                      autoComplete="street-address"
                      value={signup.street}
                      onChange={(e) => setSignup({ ...signup, street: e.target.value })}
                      data-testid="auth-street"
                    />
                  </label>
                  <label>
                    {t.number}
                    <input
                      type="text"
                      required
                      value={signup.number}
                      onChange={(e) => setSignup({ ...signup, number: e.target.value })}
                      data-testid="auth-number"
                    />
                  </label>
                  <label>
                    {t.complement}
                    <input
                      type="text"
                      value={signup.complement}
                      onChange={(e) => setSignup({ ...signup, complement: e.target.value })}
                      data-testid="auth-complement"
                    />
                  </label>
                  <label>
                    {districtLabel}
                    <input
                      type="text"
                      required={isBrazil}
                      value={signup.district}
                      onChange={(e) => setSignup({ ...signup, district: e.target.value })}
                      data-testid="auth-district"
                    />
                  </label>
                  <label>
                    {t.city}
                    <input
                      type="text"
                      required
                      autoComplete="address-level2"
                      value={signup.city}
                      onChange={(e) => setSignup({ ...signup, city: e.target.value })}
                      data-testid="auth-city"
                    />
                  </label>
                  <label>
                    {stateLabel}
                    <input
                      type="text"
                      required
                      minLength={1}
                      maxLength={isBrazil ? 2 : 80}
                      autoComplete="address-level1"
                      value={signup.state}
                      onChange={(e) =>
                        setSignup({
                          ...signup,
                          state: isBrazil
                            ? e.target.value.toUpperCase()
                            : e.target.value,
                        })
                      }
                      data-testid="auth-state"
                    />
                  </label>
                </div>
                <label className="auth-terms">
                  <input
                    type="checkbox"
                    checked={signup.accept_terms}
                    onChange={(e) => setSignup({ ...signup, accept_terms: e.target.checked })}
                    data-testid="auth-accept-terms"
                  />
                  <span>
                    {t.acceptTerms}{" "}
                    <Link to="/termos" target="_blank" rel="noreferrer">
                      {t.terms}
                    </Link>{" "}
                    e{" "}
                    <Link to="/privacidade" target="_blank" rel="noreferrer">
                      {t.privacy}
                    </Link>
                    .
                  </span>
                </label>
              </>
            )}
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
          {mode === "login" && (
            <p className="auth-foot">
              <Link
                to={`/esqueci-senha?next=${encodeURIComponent(next)}`}
                data-testid="auth-forgot"
              >
                {t.forgotPassword}
              </Link>
            </p>
          )}
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
