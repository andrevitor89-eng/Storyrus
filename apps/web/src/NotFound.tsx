import { Link } from "react-router-dom";
import { SHARED, useLang } from "./i18n";
import { SimpleShell } from "./SiteChrome";

const COPY = {
  pt: {
    title: "Página não encontrada",
    lead: "Esse endereço não existe neste site.",
    cta: "Voltar para o início",
  },
  en: {
    title: "Page not found",
    lead: "That address does not exist on this site.",
    cta: "Back to home",
  },
} as const;

export function NotFound() {
  const [lang] = useLang();
  const t = COPY[lang];
  return (
    <SimpleShell>
      <section className="page-card" aria-labelledby="nf-title">
        <p className="page-kicker">404</p>
        <h1 id="nf-title">{t.title}</h1>
        <p>{t.lead}</p>
        <Link to="/" className="kbtn kbtn-primary">{t.cta}</Link>
        <p className="page-alt">
          <Link to="/privacidade">{SHARED[lang].privacy}</Link>
          {" · "}
          <Link to="/termos">{SHARED[lang].terms}</Link>
        </p>
      </section>
    </SimpleShell>
  );
}
