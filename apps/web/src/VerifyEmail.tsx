import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import logo from "./assets/logo.png";
import { api } from "./api";
import { safeNextPath } from "./Auth";
import "./landing.css";

/**
 * Confirma o e-mail via token da query e abre sessão no estúdio.
 */
export function VerifyEmail() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = useMemo(() => (params.get("token") || "").trim(), [params]);
  const next = useMemo(() => safeNextPath(params.get("next")), [params]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token) {
        if (!cancelled) {
          setError("Link inválido. Solicite um novo cadastro.");
          setBusy(false);
        }
        return;
      }
      try {
        await api.verifyEmail(token);
        if (!cancelled) navigate(next, { replace: true });
      } catch (err) {
        if (!cancelled) {
          setError(
            ((err as Error).message || "")
              .replace(/^\d{3}:\s*/i, "")
              .trim() || "Link inválido ou expirado.",
          );
          setBusy(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate, next, token]);

  return (
    <div className="kid auth-kid" data-testid="verify-email-page">
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-logo">
            <Link to="/">
              <img src={logo} alt="Story R Us" />
            </Link>
          </div>
          <h1>Confirmando e-mail</h1>
          {busy && !error && (
            <p className="auth-lead" data-testid="verify-email-busy">
              Aguarde…
            </p>
          )}
          {error && (
            <>
              <p className="auth-error" role="alert" data-testid="verify-email-error">
                {error}
              </p>
              <p className="auth-foot">
                <Link to="/cadastro" data-testid="verify-email-signup">
                  Criar conta de novo
                </Link>
              </p>
              <p className="auth-foot">
                <Link to="/entrar" data-testid="verify-email-login">
                  Já confirmei — entrar
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
