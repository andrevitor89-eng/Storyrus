import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

type Lang = "pt" | "en";

/* ---------------- ícones da marca (SVG, sem emojis) ---------------- */
type IconProps = { className?: string };
const S = 2.2;

const IcPhoto = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="3" y="5" width="18" height="14" rx="3" />
    <circle cx="8.5" cy="10" r="1.6" />
    <path d="M4 17l4.5-4 3 2.5L15 11l5 5" />
  </svg>
);
const IcBook = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 6c-2-1.4-4.5-1.6-7-1v12c2.5-.6 5-.4 7 1 2-1.4 4.5-1.6 7-1V5c-2.5-.6-5-.4-7 1z" />
    <path d="M12 6v13" />
  </svg>
);
const IcStar = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <path d="M12 2.6l2.7 5.7 6.3.8-4.6 4.3 1.2 6.2L12 16.9 6.4 19.6l1.2-6.2L3 9.1l6.3-.8L12 2.6z" />
  </svg>
);
const IcPlay = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="12" r="9" />
    <path d="M10 8.5l6 3.5-6 3.5z" fill="currentColor" stroke="none" />
  </svg>
);
const IcGift = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="3.5" y="10" width="17" height="10.5" rx="1.6" />
    <path d="M3 10h18M12 10v10.5" />
    <path d="M12 10S9 5.5 7 6.5 8.5 10 12 10zM12 10s3-4.5 5-3.5S15.5 10 12 10z" />
  </svg>
);
const IcHeart = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 20s-7-4.4-9-8.5C1.6 8.3 3.3 5.5 6.3 5.5c1.9 0 3 1.1 3.7 2.2.7-1.1 1.8-2.2 3.7-2.2 3 0 4.7 2.8 3.3 6C19 15.6 12 20 12 20z" />
  </svg>
);
const IcBookmark = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M7 4h10a1 1 0 0 1 1 1v15l-6-3.6L6 20V5a1 1 0 0 1 1-1z" />
  </svg>
);
const IcHero = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <circle cx="12" cy="6" r="2.4" />
    <path d="M12 8.4v6M12 10l-4-1.5M12 10l4-1.5M12 14.4l-3 5M12 14.4l3 5" />
  </svg>
);
const IcHome = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M4 11l8-6 8 6M6 10v9h12v-9" />
  </svg>
);
const IcSparkle = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <path d="M12 3l1.6 5L19 9.6l-5 1.6L12 17l-1.6-5.8L5 9.6 10.4 8 12 3z" />
  </svg>
);
const IcArrow = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 40 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M4 12h28M24 4l9 8-9 8" />
  </svg>
);

const NAV_ICONS = [IcHome, IcBook, IcSparkle, IcStar, IcHeart];

/* ------- exemplos reais (foto -> ilustração). Coloque os arquivos em apps/web/public/exemplos/ ------- */
const EXAMPLES = [
  { b: "foto-bebe.jpg", a: "arte-bebe.jpg" },
  { b: "foto-menino.jpg", a: "arte-menino.jpg" },
  { b: "foto-pai.jpg", a: "arte-pai.jpg" },
];
const exUrl = (f: string) => `${import.meta.env.BASE_URL}exemplos/${f}`;

const I18N = {
  pt: {
    nav: ["Início", "Como funciona", "Histórias", "Presente", "Famílias"],
    explore: "Explorar agora",
    eyebrow: "Sua foto vira uma história",
    h_pre: "Transforme uma foto em uma ",
    w1: "história",
    c1: " onde seu filho é o ",
    w2: "herói",
    h_suf: ".",
    lead: "Você envia a foto e a gente cria um personagem ilustrado, uma história personalizada, um livrinho em PDF e até um vídeo narrado.",
    cta_play: "Criar minha história",
    cta_disc: "Ver como funciona",
    trust: "Encantando famílias do início ao fim",
    ba_before: "ANTES",
    ba_after: "DEPOIS",
    ba_caption: "Você envia a foto. A gente cria o encanto.",
    hiw_title: "Como funciona",
    hiw_sub: "Três passos simples, do jeitinho que você vê nas nossas artes.",
    hiw: [
      { t: "Você envia a foto", p: "Uma foto da criança já basta para começar." },
      { t: "Criamos a história", p: "O personagem ganha vida e a história é escrita só para vocês." },
      { t: "Sua família é a estrela", p: "Vocês são os protagonistas — para guardar para sempre." },
    ],
    out_title: "O que você recebe",
    out_sub: "Tudo pronto para ler, assistir e guardar.",
    outputs: [
      { t: "E-book ilustrado", p: "Um livrinho em PDF, página a página, para baixar." },
      { t: "Vídeo narrado", p: "A história ganha voz para emocionar a família." },
      { t: "Lembrança para sempre", p: "Um presente único que fica de recordação." },
    ],
    features: ["Histórias personalizadas", "Conexão em família", "Memórias que ficam para sempre", "Um presente inesquecível"],
    band_title: "Pronto para virar protagonista?",
    band_sub: "Envie sua foto e receba uma história única, criada só para você.",
    band_cta: "Criar minha história",
    tagline: "Feito com amor. Criado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  en: {
    nav: ["Home", "How it works", "Stories", "Gift", "Families"],
    explore: "Explore now",
    eyebrow: "Your photo becomes a story",
    h_pre: "Turn a photo into a ",
    w1: "story",
    c1: " where your child is the ",
    w2: "hero",
    h_suf: ".",
    lead: "You send the photo and we create an illustrated character, a personalized story, a PDF book and even a narrated video.",
    cta_play: "Create my story",
    cta_disc: "See how it works",
    trust: "Delighting families from start to finish",
    ba_before: "BEFORE",
    ba_after: "AFTER",
    ba_caption: "You send the photo. We create the magic.",
    hiw_title: "How it works",
    hiw_sub: "Three simple steps, just like you see in our artwork.",
    hiw: [
      { t: "You send the photo", p: "One photo of your child is all it takes to begin." },
      { t: "We create the story", p: "The character comes to life and the story is written just for you." },
      { t: "Your family is the star", p: "You are the heroes — made to keep forever." },
    ],
    out_title: "What you get",
    out_sub: "Ready to read, watch and keep.",
    outputs: [
      { t: "Illustrated e-book", p: "A PDF book, page by page, ready to download." },
      { t: "Narrated video", p: "The story gets a voice to move the whole family." },
      { t: "A forever keepsake", p: "A unique gift to treasure." },
    ],
    features: ["Personalized stories", "Family connection", "Memories that last forever", "An unforgettable gift"],
    band_title: "Ready to become the hero?",
    band_sub: "Send your photo and get a unique story, made just for you.",
    band_cta: "Create my story",
    tagline: "Made with love. Created to enchant.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
} as const;

export function Landing() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [lang, setLang] = useState<Lang>("pt");
  const [ex, setEx] = useState(0);
  const t = I18N[lang];
  const navHrefs = ["#top", "#como", "#historias", "#presente", "#familias"];
  const outIcons = [IcBook, IcPlay, IcGift];
  const featIcons = [IcHero, IcHeart, IcBookmark, IcGift];

  useEffect(() => {
    const id = setInterval(() => setEx((v) => (v + 1) % EXAMPLES.length), 6500);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const els = rootRef.current?.querySelectorAll(".reveal") ?? [];
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add("in");
            io.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12 },
    );
    els.forEach((el, i) => {
      (el as HTMLElement).style.transitionDelay = `${(i % 3) * 0.1}s`;
      io.observe(el);
    });
    return () => io.disconnect();
  }, []);

  const closeNav = () => setNavOpen(false);
  const cur = EXAMPLES[ex];

  return (
    <div className="kid" ref={rootRef} id="top">
      {/* ceu decorativo: estrelas e luas (sem emojis) */}
      <div className="sky" aria-hidden>
        <IcStar className="dstar d1" />
        <IcStar className="dstar d2" />
        <IcSparkle className="dstar d3" />
        <IcStar className="dstar d4" />
        <svg className="dmoon m1" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#f4b740" /></svg>
        <svg className="dmoon m2" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#7fb2e3" /></svg>
      </div>

      <header className="knav">
        <a href="#top" className="kbrand"><img src={logo} alt="Story.R.Us" /></a>
        <nav className={`klinks${navOpen ? " open" : ""}`}>
          {t.nav.map((label, i) => {
            const Icon = NAV_ICONS[i];
            return (
              <a key={label} href={navHrefs[i]} onClick={closeNav}>
                <Icon className="ni" />
                {label}
              </a>
            );
          })}
          <Link to="/app" className="kbtn kbtn-go" onClick={closeNav}>{t.explore}</Link>
        </nav>
        <div className="kright">
          <div className="lang" role="group" aria-label="Idioma / Language">
            <button className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")}>PT</button>
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
          </div>
          <button className="khamb" aria-label="Menu" onClick={() => setNavOpen((v) => !v)}>☰</button>
        </div>
      </header>

      {/* ---------------- HERO com Antes/Depois (fotos reais) ---------------- */}
      <section className="khero">
        <div className="khero-text">
          <span className="keyebrow"><IcSparkle className="ei" /> {t.eyebrow}</span>
          <h1>
            {t.h_pre}<span className="g1">{t.w1}</span>{t.c1}<span className="g3">{t.w2}</span>{t.h_suf}
          </h1>
          <p className="klead">{t.lead}</p>
          <div className="khero-cta">
            <Link to="/app" className="kbtn kbtn-primary">{t.cta_play}</Link>
            <a href="#como" className="kbtn kbtn-soft">{t.cta_disc}</a>
          </div>
          <div className="ktrust"><span className="stars">★★★★★</span> {t.trust}</div>
        </div>

        <div className="khero-art">
          <div className="banner" key={ex}>
            <img className="layer layer-before" src={exUrl(cur.b)} alt="Foto enviada" loading="eager" />
            <img className="layer layer-after" src={exUrl(cur.a)} alt="Ilustração criada" loading="eager" />
            <span className="grain" />
            <span className="ba-tag tag-before">{t.ba_before}</span>
            <span className="ba-tag tag-after">{t.ba_after}</span>
            <span className="reveal-line"><span className="reveal-knob"><IcArrow /></span></span>
            <span className="sp sp1"><IcSparkle /></span>
            <span className="sp sp2"><IcStar /></span>
            <span className="sp sp3"><IcSparkle /></span>
          </div>
          <div className="ba-dots">
            {EXAMPLES.map((_, k) => (
              <button key={k} className={k === ex ? "on" : ""} onClick={() => setEx(k)} aria-label={`Exemplo ${k + 1}`} />
            ))}
          </div>
          <div className="ba-caption"><IcHeart className="ci" /> {t.ba_caption}</div>
        </div>
      </section>

      {/* ---------------- COMO FUNCIONA (fluxo animado) ---------------- */}
      <section className="ksection" id="como">
        <h2 className="ktitle reveal">{t.hiw_title}</h2>
        <p className="ksub reveal">{t.hiw_sub}</p>
        <div className="flow">
          {t.hiw.map((s, i) => {
            const Icon = [IcPhoto, IcBook, IcStar][i];
            return (
              <div className="flow-item" key={s.t}>
                <div className="flow-step reveal">
                  <div className="flow-badge"><Icon className="fi" /><span className="flow-num">{i + 1}</span></div>
                  <h3>{s.t}</h3>
                  <p>{s.p}</p>
                </div>
                {i < t.hiw.length - 1 && <span className="flow-arrow" aria-hidden><IcArrow /></span>}
              </div>
            );
          })}
        </div>
      </section>

      {/* ---------------- O QUE VOCE RECEBE ---------------- */}
      <section className="ksection soft-wrap" id="historias">
        <h2 className="ktitle reveal">{t.out_title}</h2>
        <p className="ksub reveal">{t.out_sub}</p>
        <div className="kgrid outputs">
          {t.outputs.map((o, i) => {
            const Icon = outIcons[i];
            return (
              <div className="kcard reveal" key={o.t}>
                <div className="kicon"><Icon className="ki" /></div>
                <h3>{o.t}</h3>
                <p>{o.p}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ---------------- FAIXA DE ATRIBUTOS ---------------- */}
      <section className="featurebar" id="presente">
        {t.features.map((f, i) => {
          const Icon = featIcons[i];
          return (
            <div className="feat" key={f}>
              <Icon className="feat-ic" />
              <span>{f}</span>
            </div>
          );
        })}
      </section>

      {/* ---------------- CTA ---------------- */}
      <section className="kband" id="familias">
        <IcSparkle className="twk b1" />
        <IcStar className="twk b2" />
        <h2>{t.band_title}</h2>
        <p>{t.band_sub}</p>
        <Link to="/app" className="kbtn kbtn-primary big">{t.band_cta}</Link>
      </section>

      {/* ---------------- FOOTER ---------------- */}
      <footer className="kfoot">
        <div className="kfoot-nav">
          {t.nav.map((label, i) => {
            const Icon = NAV_ICONS[i];
            return (
              <a key={label} href={navHrefs[i]}><Icon className="ni" />{label}</a>
            );
          })}
        </div>
        <p className="kfoot-tag"><IcHeart className="ci" /> {t.tagline}</p>
        <p className="kfoot-copy">{t.foot_copy}</p>
      </footer>
    </div>
  );
}
