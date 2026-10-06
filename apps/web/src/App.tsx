import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { accountGateHref } from "./Auth";
import { api, getToken } from "./api";
import { staticPageMeta, usePageMeta } from "./pageMeta";
import { Studio } from "./Studio";

function demoIdFromSearch(search: string): string | null {
  const q = new URLSearchParams(search);
  const ex = q.get("exemplo");
  return ex && ex.trim() ? ex.trim() : null;
}

/**
 * Estúdio exige conta registrada (exceto visualização de exemplo ?exemplo=).
 * Sem token, guest ou e-mail não confirmado → cadastro (sessão inválida é limpa).
 */
export function App() {
  usePageMeta(staticPageMeta("/app"));
  const location = useLocation();
  const navigate = useNavigate();
  const isDemo = Boolean(demoIdFromSearch(location.search));
  const [gate, setGate] = useState<"loading" | "ok" | "need-account">(
    isDemo ? "ok" : "loading",
  );

  useEffect(() => {
    if (isDemo) {
      setGate("ok");
      return;
    }
    let cancelled = false;
    (async () => {
      if (!getToken()) {
        if (!cancelled) setGate("need-account");
        return;
      }
      try {
        const me = await api.me();
        if (cancelled) return;
        if (me.is_guest || !me.email_verified) {
          api.logout();
          setGate("need-account");
          return;
        }
        setGate("ok");
      } catch {
        api.logout();
        if (!cancelled) setGate("need-account");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isDemo, location.search]);

  if (gate === "loading") return null;
  if (gate === "need-account") {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={accountGateHref(next)} replace />;
  }

  return (
    <Studio
      onLogout={() => {
        api.logout();
        navigate("/entrar", { replace: true });
      }}
    />
  );
}
