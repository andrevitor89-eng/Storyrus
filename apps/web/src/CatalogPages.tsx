import { useEffect, useState, type CSSProperties } from "react";
import { Link, useParams } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";
import { NotFound } from "./NotFound";
import {
  CatalogBookCard,
  catalogCategory,
  catalogEntry,
  catalogPageCopy,
  catalogSections,
  readSiteLang,
  type Lang,
} from "./Landing";

function useSiteLang() {
  const [lang, setLang] = useState<Lang>(readSiteLang);
  useEffect(() => {
    document.documentElement.lang = lang === "en" ? "en" : lang === "es" ? "es" : "pt-BR";
    try { localStorage.setItem("lang", lang); } catch { /* ignore */ }
  }, [lang]);
  useEffect(() => {
    try {
      const theme = localStorage.getItem("theme");
      if (theme === "light" || theme === "dark") document.documentElement.setAttribute("data-theme", theme);
    } catch { /* ignore */ }
  }, []);
  return [lang, setLang] as const;
}

function LangSwitch({ lang, setLang }: { lang: Lang; setLang: (lang: Lang) => void }) {
  return (
    <div className="lang" role="group" aria-label="Idioma / Language / Idioma">
      <button className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")} data-testid="landing-lang-pt">PT</button>
      <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")} data-testid="landing-lang-en">EN</button>
      <button className={lang === "es" ? "on" : ""} onClick={() => setLang("es")} data-testid="landing-lang-es">ES</button>
    </div>
  );
}

export function CatalogPage() {
  const [lang, setLang] = useSiteLang();
  const copy = catalogPageCopy(lang);
  const sections = catalogSections(lang);
  useEffect(() => {
    const id = window.location.hash.replace("#", "");
    if (!id) return;
    document.getElementById(id)?.scrollIntoView();
  }, [sections]);
  return (
    <div className="kid">
      <header className="knav">
        <Link to="/" className="kbrand"><img src={logo} alt="Story.R.Us" /></Link>
        <LangSwitch lang={lang} setLang={setLang} />
      </header>
      <main className="ksection catalog-page" id="catalogo">
        <h1 className="ktitle">{copy.title}</h1>
        {sections.map((section) => (
          <section key={section.id} id={section.id} className="catalog-section" style={{ "--group": section.color } as CSSProperties}>
            <h2 className="catalog-section-title">{section.name}</h2>
            <div className="cat-grid">
              {section.books.map((book) => (
                <CatalogBookCard key={book.catalogI} book={book} lang={lang} personalize={copy.personalize} />
              ))}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}

export function CategoryCatalogPage() {
  const [lang, setLang] = useSiteLang();
  const params = useParams();
  const section = catalogCategory(lang, params.categoria ?? "");
  if (!section) return <NotFound />;
  const copy = catalogPageCopy(lang);
  return (
    <div className="kid">
      <header className="knav">
        <Link to="/" className="kbrand"><img src={logo} alt="Story.R.Us" /></Link>
        <LangSwitch lang={lang} setLang={setLang} />
      </header>
      <main className="ksection catalog-page" id="catalogo">
        <p className="book-back"><Link to="/catalogo">{copy.back}</Link></p>
        <section className="catalog-section" id={section.id} style={{ "--group": section.color } as CSSProperties}>
          <h1 className="catalog-section-title">{section.name}</h1>
          {section.books.length > 0 ? (
            <div className="cat-grid">
              {section.books.map((book) => (
                <CatalogBookCard key={book.catalogI} book={book} lang={lang} personalize={copy.personalize} />
              ))}
            </div>
          ) : (
            <p className="kcat-empty">{copy.empty}</p>
          )}
        </section>
      </main>
    </div>
  );
}

export function BookPage() {
  const [lang, setLang] = useSiteLang();
  const params = useParams();
  const index = Number(params.indice);
  const book = Number.isInteger(index) ? catalogEntry(lang, index) : null;
  if (!book) return <NotFound />;
  const copy = catalogPageCopy(lang);
  return (
    <div className="kid">
      <header className="knav">
        <Link to="/" className="kbrand"><img src={logo} alt="Story.R.Us" /></Link>
        <LangSwitch lang={lang} setLang={setLang} />
      </header>
      <main className="ksection book-page" id="catalogo">
        <p className="book-back"><Link to={`/catalogo/${book.sectionId}`}>{copy.back}</Link></p>
        <div className="book-page-card">
          <CatalogBookCard book={book} lang={lang} personalize={copy.personalize} linkBook={false} layout="page" />
        </div>
      </main>
    </div>
  );
}
