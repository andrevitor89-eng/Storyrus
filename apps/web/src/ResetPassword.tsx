import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import logo from "./assets/logo.png";
import { api } from "./api";
import { safeNextPath } from "./Auth";
import "./landing.css";

/**
 * Define nova senha a partir do token do e-mail e abre sessão no estúdio.
 */
export function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = useMemo(() => (params.get("token") || "").trim(), [params]);
  const next = useMemo(() => safeNextPath(params.get("next")), [params]);
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) {
      setError("Link inválido. Solicite um novo em Esqueci a senha.");
      return;
    }
    if (password !== passwordConfirm) {
      setError("As senhas não coincidem.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.resetPassword(token, password, passwordConfirm);
      navigate(next, { replace: true });
    } catch (err) {
      const msg = ((err as Error).message || "").trim();
      if (
        /^502\b|^503\b|^504\b/i.test(msg) ||
        /failed to fetch|networkerror|load failed|demorou demais|abort/i.test(msg)
      ) {
        setError("Não foi possível redefinir agora. Tente de novo em instantes.");
      } else {
        setError(
          msg.replace(/^\d{3}:\s*/i, "").trim() || "Link inválido ou expirado.",
        );
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="kid auth-kid" data-testid="reset-password-page">
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-logo">
            <Link to="/">
              <img src={logo} alt="Story R Us" />
            </Link>
          </div>
          <h1>Nova senha</h1>
          <p className="auth-lead">Escolha uma senha nova para a sua conta.</p>
          {!token ? (
            <>
              <p className="auth-error" role="alert" data-testid="reset-password-error">
                Link inválido. Solicite um novo em Esqueci a senha.
              </p>
              <p className="auth-foot">
                <Link to="/esqueci-senha" data-testid="reset-password-forgot">
                  Esqueci a senha
                </Link>
              </p>
            </>
          ) : (
            <form className="auth-form" onSubmit={onSubmit} data-testid="reset-password-form">
              <label>
                Nova senha (mín. 8)
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  data-testid="reset-password-password"
                />
              </label>
              <label>
                Confirmar senha
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  data-testid="reset-password-confirm"
                />
              </label>
              {error && (
                <p className="auth-error" role="alert" data-testid="reset-password-error">
                  {error}
                </p>
              )}
              <button
                type="submit"
                className="kbtn kbtn-primary auth-cta"
                disabled={busy}
                data-testid="reset-password-submit"
              >
                {busy ? "Aguarde…" : "Salvar senha"}
              </button>
            </form>
          )}
          <p className="auth-foot">
            <Link to="/entrar" data-testid="reset-password-login">
              Voltar ao login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
