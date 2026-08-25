import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import { SHARED, useLang, useTheme, type Lang } from "./i18n";

type IconProps = { className?: string };
const Svg = (p: { className?: string; children: ReactNode }) => (
  <svg className={p.className} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden>{p.children}</svg>
);
const IcSun = ({ className }: IconProps) => (
  <Svg className={className}><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" /></Svg>
);
const IcMoon = ({ className }: IconProps) => (
  <Svg className={className}><path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" /></Svg>
);
const IcHeart = ({ className }: IconProps) => (
  <Svg className={className}><path d="M12 20s-7-4.4-9-8.5C1.6 8.3 3.3 5.5 6.3 5.5c1.9 0 3 1.1 3.7 2.2.7-1.1 1.8-2.2 3.7-2.2 3 0 4.7 2.8 3.3 6C19 15.6 12 20 12 20z" /></Svg>
);

export function LangToggle({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  return (
    <div className="lang" role="group" aria-label={SHARED[lang].lang_label}>
      <button type="button" className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")}>PT</button>
      <button type="button" className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
    </div>
  );
}

export function ThemeToggle({ theme, setTheme, label }: {
  theme: "light" | "dark";
  setTheme: (t: "light" | "dark") => void;
  label: string;
}) {
  return (
    <button type="button" className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={label}>
      {theme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
    </button>
  );
}

export function SiteFooter({ lang, extra }: { lang: Lang; extra?: ReactNode }) {
  const t = SHARED[lang];
  return (
    <footer className="kfoot">
      {extra}
      <div className="kfoot-legal">
        <Link to="/privacidade">{t.privacy}</Link>
        <Link to="/termos">{t.terms}</Link>
      </div>
      <p className="kfoot-tag"><IcHeart className="ci" /> {t.tagline}</p>
      <p className="kfoot-copy">{t.foot_copy}</p>
    </footer>
  );
}

export function SimpleHeader({ lang, setLang, homeHref = "/" }: {
  lang: Lang;
  setLang: (l: Lang) => void;
  homeHref?: string;
}) {
  const [theme, setTheme] = useTheme();
  const t = SHARED[lang];
  return (
    <header className="knav">
      <Link to={homeHref} className="kbrand"><img src={logo} alt="Story R Us" /></Link>
      <div className="kright">
        <ThemeToggle theme={theme} setTheme={setTheme} label={t.theme_label} />
        <LangToggle lang={lang} setLang={setLang} />
      </div>
    </header>
  );
}

export function SimpleShell({ children }: { children: ReactNode }) {
  const [lang, setLang] = useLang();
  return (
    <div className="kid">
      <SimpleHeader lang={lang} setLang={setLang} />
      <main className="page-main">{children}</main>
      <SiteFooter lang={lang} />
    </div>
  );
}

export { useLang, useTheme };
