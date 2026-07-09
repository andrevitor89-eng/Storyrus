import { useEffect, useRef, useState, type MouseEvent as RMouseEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

type Lang = "pt" | "en";

/* ---------------- ícones (SVG, sem emojis) ---------------- */
type IconProps = { className?: string };
const S = 2.2;
const Svg = (p: { className?: string; children: ReactNode; fill?: string }) => (
  <svg className={p.className} viewBox="0 0 24 24" fill={p.fill ?? "none"} stroke={p.fill ? "none" : "currentColor"}
    strokeWidth={S} strokeLinecap="round" strokeLinejoin="round" aria-hidden>{p.children}</svg>
);
const IcBook =({ className }: IconProps) => (<Svg className={className}><path d="M12 6c-2-1.4-4.5-1.6-7-1v12c2.5-.6 5-.4 7 1 2-1.4 4.5-1.6 7-1V5c-2.5-.6-5-.4-7 1z" /><path d="M12 6v13" /></Svg>);
const IcStar = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 2.6l2.7 5.7 6.3.8-4.6 4.3 1.2 6.2L12 16.9 6.4 19.6l1.2-6.2L3 9.1l6.3-.8L12 2.6z" /></svg>);
const IcPlay = ({ className }: IconProps) => (<Svg className={className}><circle cx="12" cy="12" r="9" /><path d="M10 8.5l6 3.5-6 3.5z" fill="currentColor" stroke="none" /></Svg>);
const IcFilm = ({ className }: IconProps) => (<Svg className={className}><rect x="4" y="5" width="16" height="14" rx="2" /><path d="M9 5v14M15 5v14" /><path d="M4 9h5M4 13h5M15 9h5M15 13h5" /></Svg>);
const IcPrinter = ({ className }: IconProps) => (<Svg className={className}><path d="M7 9V4h10v5" /><rect x="4" y="9" width="16" height="7" rx="2" /><path d="M8 14h8v6H8z" /><circle cx="17" cy="12" r="0.9" fill="currentColor" stroke="none" /></Svg>);
const IcGift = ({ className }: IconProps) => (<Svg className={className}><rect x="3.5" y="10" width="17" height="10.5" rx="1.6" /><path d="M3 10h18M12 10v10.5" /><path d="M12 10S9 5.5 7 6.5 8.5 10 12 10zM12 10s3-4.5 5-3.5S15.5 10 12 10z" /></Svg>);
const IcHeart = ({ className }: IconProps) => (<Svg className={className}><path d="M12 20s-7-4.4-9-8.5C1.6 8.3 3.3 5.5 6.3 5.5c1.9 0 3 1.1 3.7 2.2.7-1.1 1.8-2.2 3.7-2.2 3 0 4.7 2.8 3.3 6C19 15.6 12 20 12 20z" /></Svg>);
const IcHome = ({ className }: IconProps) => (<Svg className={className}><path d="M4 11l8-6 8 6M6 10v9h12v-9" /></Svg>);
const IcSparkle = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 3l1.6 5L19 9.6l-5 1.6L12 17l-1.6-5.8L5 9.6 10.4 8 12 3z" /></svg>);
const IcArrow = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 40 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 12h28M24 4l9 8-9 8" /></svg>);
const IcSun = ({ className }: IconProps) => (<Svg className={className}><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" /></Svg>);
const IcMoon = ({ className }: IconProps) => (<Svg className={className}><path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" /></Svg>);

const NAV_ICONS = [IcHome, IcBook, IcSparkle, IcGift, IcHeart];

/* ------- exemplos reais em apps/web/public/exemplos/ ------- */
const EXAMPLES = [
  { b: "foto-bebe.jpg", a: "arte-bebe.jpg" },
  { b: "foto-menino.jpg", a: "arte-menino.jpg" },
  { b: "foto-pai.jpg", a: "arte-pai.jpg" },
];
const HOW_IMGS = ["foto-menino.jpg", "arte-menino.jpg", "livro-2.jpg"];
const BOOK = ["livro-1.jpg", "livro-2.jpg", "livro-3.jpg", "livro-4.jpg", "livro-5.jpg"];
const exUrl = (f: string) => `${import.meta.env.BASE_URL}exemplos/${f}`;

function FlipBook({ pages }: { pages: string[] }) {
  const [i, setI] = useState(0);
  const [anim, setAnim] = useState<"next" | "prev" | null>(null);
  const [target, setTarget] = useState(0);
  const flip = (dir: "next" | "prev") => {
    if (anim) return;
    const t = dir === "next" ? i + 1 : i - 1;
    if (t < 0 || t >= pages.length) return;
    setTarget(t);
    setAnim(dir);
    window.setTimeout(() => { setI(t); setAnim(null); }, 720);
  };
  const baseSrc = anim === "next" ? pages[target] : pages[i];
  const turnSrc = anim === "next" ? pages[i] : pages[target];
  const onStage = (e: RMouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (e.clientX - r.left > r.width / 2) flip("next"); else flip("prev");
  };
  return (
    <div className="flipbook">
      <button className="fb-nav" onClick={() => flip("prev")} disabled={i === 0} aria-label="Página anterior">‹</button>
      <div className="fb-stage" onClick={onStage} role="button" tabIndex={0} aria-label="Virar página">
        <span className="fb-spine" />
        <img className="fb-page fb-base" src={exUrl(baseSrc)} alt={`Página ${i + 1}`} />
        {anim && <img className={`fb-page fb-turn ${anim}`} src={exUrl(turnSrc)} alt="" aria-hidden />}
        <span className="fb-count">{i + 1} / {pages.length}</span>
      </div>
      <button className="fb-nav" onClick={() => flip("next")} disabled={i === pages.length - 1} aria-label="Próxima página">›</button>
    </div>
  );
}

const I18N = {
  pt: {
    nav: ["Início", "Como funciona", "Exemplo", "Formatos", "Avaliações"],
    explore: "Explorar agora",
    eyebrow: "Sua foto vira uma história",
    h_pre: "Transforme uma foto em uma ", w1: "história", c1: " onde seu filho é o ", w2: "herói", h_suf: ".",
    lead: "Você envia a foto e a gente cria um personagem ilustrado, uma história personalizada, um livro em PDF e até um vídeo narrado.",
    cta_play: "Criar minha história", cta_disc: "Ver como funciona",
    trust: "Encantando famílias do início ao fim",
    ba_before: "ANTES", ba_after: "DEPOIS", ba_caption: "Você envia a foto. A gente cria o encanto.",
    hiw_title: "Como funciona", hiw_sub: "Da sua foto ao livro — com exemplos reais.",
    hiw: [
      { t: "Você envia a foto", p: "Uma foto da criança já basta para começar." },
      { t: "Criamos o personagem e a história", p: "Ilustração fiel à foto e um texto só de vocês." },
      { t: "Sua família vira o livro", p: "Páginas ilustradas, para guardar para sempre." },
    ],
    book_badge: "Exemplo real",
    story_title: "Folheie um livro de verdade",
    story_sub: "Um livro criado pela plataforma a partir de uma única foto.",
    story_hint: "Clique nas laterais do livro (ou use as setas) para virar as páginas.",
    fmt_title: "Escolha o formato", fmt_sub: "Do mesmo personagem, três formas de guardar a história.",
    formats: [
      { t: "Livro para impressão", price: "R$ 49", unit: "por livro", p: "Um livro ilustrado em PDF, pronto para imprimir e ter na estante.", feats: ["Capa + páginas ilustradas", "PDF em alta para impressão", "Personagem fiel à foto"], cta: "Criar meu livro", badge: "Mais amado" },
      { t: "Vídeo narrado", price: "R$ 89", unit: "por vídeo", p: "A história ganha voz e trilha, perfeita para assistir em família.", feats: ["Narração encantadora", "Cenas ilustradas", "Fácil de compartilhar"], cta: "Criar meu vídeo", badge: "" },
      { t: "Animação", price: "R$ 149", unit: "por animação", p: "O personagem ganha vida numa animação cheia de magia.", feats: ["Movimento e magia", "Baseada na sua história", "Um presente diferente"], cta: "Criar animação", badge: "" },
    ],
    rev_title: "O que as famílias dizem", rev_sub: "Histórias que viraram memórias para sempre.",
    reviews: [
      { q: "Meu filho pede para ler o livro dele toda noite. Emocionante vê-lo como herói!", name: "Ana C." },
      { q: "Enviei uma foto e recebi um livro lindo. Virou o presente de aniversário da vovó.", name: "Rafael M." },
      { q: "A ilustração ficou idêntica ao meu bebê. Vamos guardar para sempre.", name: "Juliana P." },
      { q: "O vídeo narrado fez a família toda se emocionar. Vale cada segundo.", name: "Marcos e Bia" },
    ],
    features: ["Histórias personalizadas", "Conexão em família", "Memórias que ficam para sempre", "Um presente inesquecível"],
    band_title: "Pronto para virar protagonista?",
    band_sub: "Envie sua foto e receba uma história única, criada só para você.",
    band_cta: "Criar minha história",
    tagline: "Feito com amor. Criado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  en: {
    nav: ["Home", "How it works", "Example", "Formats", "Reviews"],
    explore: "Explore now",
    eyebrow: "Your photo becomes a story",
    h_pre: "Turn a photo into a ", w1: "story", c1: " where your child is the ", w2: "hero", h_suf: ".",
    lead: "You send the photo and we create an illustrated character, a personalized story, a PDF book and even a narrated video.",
    cta_play: "Create my story", cta_disc: "See how it works",
    trust: "Delighting families from start to finish",
    ba_before: "BEFORE", ba_after: "AFTER", ba_caption: "You send the photo. We create the magic.",
    hiw_title: "How it works", hiw_sub: "From your photo to the book — with real examples.",
    hiw: [
      { t: "You send the photo", p: "One photo of your child is all it takes to begin." },
      { t: "We create the character and story", p: "An illustration true to the photo and a story that's all yours." },
      { t: "Your family becomes the book", p: "Illustrated pages, made to keep forever." },
    ],
    book_badge: "Real example",
    story_title: "Flip through a real book",
    story_sub: "A book created by the platform from a single photo.",
    story_hint: "Click the sides of the book (or use the arrows) to turn the pages.",
    fmt_title: "Choose the format", fmt_sub: "From the same character, three ways to keep the story.",
    formats: [
      { t: "Printable book", price: "$29", unit: "per book", p: "An illustrated PDF book, ready to print and keep on the shelf.", feats: ["Cover + illustrated pages", "High-res PDF for printing", "Character true to the photo"], cta: "Create my book", badge: "Most loved" },
      { t: "Narrated video", price: "$49", unit: "per video", p: "The story gets a voice and music, perfect to watch together.", feats: ["Enchanting narration", "Illustrated scenes", "Easy to share"], cta: "Create my video", badge: "" },
      { t: "Animation", price: "$79", unit: "per animation", p: "The character comes alive in a magical animation.", feats: ["Movement and magic", "Based on your story", "A different gift"], cta: "Create animation", badge: "" },
    ],
    rev_title: "What families say", rev_sub: "Stories that became memories forever.",
    reviews: [
      { q: "My son asks to read his book every night. Seeing him as the hero is moving!", name: "Ana C." },
      { q: "I sent a photo and got a beautiful book. It became grandma's birthday gift.", name: "Rafael M." },
      { q: "The illustration looks just like my baby. We'll keep it forever.", name: "Juliana P." },
      { q: "The narrated video moved the whole family. Worth every second.", name: "Marcos & Bia" },
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
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try { const s = localStorage.getItem("theme"); if (s === "light" || s === "dark") return s; } catch { /* ignore */ }
    return "dark";
  });
  const [ex, setEx] = useState(0);
  const t = I18N[lang];
  const navHrefs = ["#top", "#como", "#historia-exemplo", "#formatos", "#reviews"];
  const fmtIcons = [IcPrinter, IcPlay, IcFilm];
  const featIcons = [IcSparkle, IcHeart, IcBook, IcGift];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);

  useEffect(() => {
    const id = setInterval(() => setEx((v) => (v + 1) % EXAMPLES.length), 6500);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const els = rootRef.current?.querySelectorAll(".reveal") ?? [];
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    els.forEach((el, i) => { (el as HTMLElement).style.transitionDelay = `${(i % 3) * 0.1}s`; io.observe(el); });
    return () => io.disconnect();
  }, []);

  const closeNav = () => setNavOpen(false);
  const cur = EXAMPLES[ex];

  return (
    <div className="kid" ref={rootRef} id="top">
      <div className="sky" aria-hidden>
        <IcStar className="dstar d1" /><IcStar className="dstar d2" /><IcSparkle className="dstar d3" /><IcStar className="dstar d4" />
        <svg className="dmoon m1" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#f4b740" /></svg>
        <svg className="dmoon m2" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#7fb2e3" /></svg>
      </div>

      <header className="knav">
        <a href="#top" className="kbrand"><img src={logo} alt="Story.R.Us" /></a>
        <nav className={`klinks${navOpen ? " open" : ""}`}>
          {t.nav.map((label, i) => {
            const Icon = NAV_ICONS[i];
            return (<a key={label} href={navHrefs[i]} onClick={closeNav}><Icon className="ni" />{label}</a>);
          })}
          <Link to="/app" className="kbtn kbtn-go" onClick={closeNav}>{t.explore}</Link>
        </nav>
        <div className="kright">
          <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Alternar tema claro/escuro">
            {theme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
          </button>
          <div className="lang" role="group" aria-label="Idioma / Language">
            <button className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")}>PT</button>
            <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
          </div>
          <button className="khamb" aria-label="Menu" onClick={() => setNavOpen((v) => !v)}>☰</button>
        </div>
      </header>

      {/* HERO */}
      <section className="khero">
        <div className="khero-text">
          <span className="keyebrow"><IcSparkle className="ei" /> {t.eyebrow}</span>
          <h1>{t.h_pre}<span className="g1">{t.w1}</span>{t.c1}<span className="g3">{t.w2}</span>{t.h_suf}</h1>
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
            <span className="sp sp1"><IcSparkle /></span><span className="sp sp2"><IcStar /></span><span className="sp sp3"><IcSparkle /></span>
          </div>
          <div className="ba-dots">
            {EXAMPLES.map((_, k) => (<button key={k} className={k === ex ? "on" : ""} onClick={() => setEx(k)} aria-label={`Exemplo ${k + 1}`} />))}
          </div>
          <div className="ba-caption"><IcHeart className="ci" /> {t.ba_caption}</div>
        </div>
      </section>

      {/* COMO FUNCIONA — com exemplos reais */}
      <section className="ksection" id="como">
        <h2 className="ktitle reveal">{t.hiw_title}</h2>
        <p className="ksub reveal">{t.hiw_sub}</p>
        <div className="howex">
          {t.hiw.map((h, i) => (
            <div className="howex-item" key={h.t}>
              <figure className="howex-card reveal">
                <img src={exUrl(HOW_IMGS[i])} alt={h.t} loading="lazy" />
                <span className="howex-num">{i + 1}</span>
                <figcaption><h3>{h.t}</h3><p>{h.p}</p></figcaption>
              </figure>
              {i < t.hiw.length - 1 && <span className="howex-arrow" aria-hidden><IcArrow /></span>}
            </div>
          ))}
        </div>
      </section>

      {/* FLIPBOOK — destaque */}
      <section className="ksection featured-book" id="historia-exemplo">
        <span className="book-badge reveal"><IcStar className="bi" /> {t.book_badge}</span>
        <h2 className="ktitle reveal">{t.story_title}</h2>
        <p className="ksub reveal">{t.story_sub}</p>
        <div className="reveal"><FlipBook pages={BOOK} /></div>
        <p className="fb-hint reveal">{t.story_hint}</p>
      </section>

      {/* FORMATOS — 3 colunas */}
      <section className="ksection" id="formatos">
        <h2 className="ktitle reveal">{t.fmt_title}</h2>
        <p className="ksub reveal">{t.fmt_sub}</p>
        <div className="fmt-grid">
          {t.formats.map((f, i) => {
            const Icon = fmtIcons[i];
            return (
              <div className={`fmt-card reveal${f.badge ? " featured" : ""}`} key={f.t}>
                {f.badge && <span className="fmt-badge">{f.badge}</span>}
                <div className="fmt-ic"><Icon /></div>
                <h3>{f.t}</h3>
                <div className="fmt-price">{f.price}<span>{f.unit}</span></div>
                <p>{f.p}</p>
                <ul className="fmt-feats">{f.feats.map((x) => <li key={x}>{x}</li>)}</ul>
                <Link to="/app" className="kbtn kbtn-primary">{f.cta}</Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* AVALIAÇÕES */}
      <section className="ksection" id="reviews">
        <h2 className="ktitle reveal">{t.rev_title}</h2>
        <p className="ksub reveal">{t.rev_sub}</p>
        <div className="rev-grid">
          {t.reviews.map((r) => (
            <figure className="rev-card reveal" key={r.name}>
              <div className="rev-stars">★★★★★</div>
              <blockquote>{r.q}</blockquote>
              <figcaption><span className="rev-av">{r.name.charAt(0)}</span>{r.name}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      {/* FAIXA DE ATRIBUTOS */}
      <section className="featurebar" id="presente">
        {t.features.map((f, i) => {
          const Icon = featIcons[i];
          return (<div className="feat" key={f}><Icon className="feat-ic" /><span>{f}</span></div>);
        })}
      </section>

      {/* CTA */}
      <section className="kband" id="familias">
        <IcSparkle className="twk b1" /><IcStar className="twk b2" />
        <h2>{t.band_title}</h2><p>{t.band_sub}</p>
        <Link to="/app" className="kbtn kbtn-primary big">{t.band_cta}</Link>
      </section>

      {/* FOOTER */}
      <footer className="kfoot">
        <div className="kfoot-nav">
          {t.nav.map((label, i) => { const Icon = NAV_ICONS[i]; return (<a key={label} href={navHrefs[i]}><Icon className="ni" />{label}</a>); })}
        </div>
        <p className="kfoot-tag"><IcHeart className="ci" /> {t.tagline}</p>
        <p className="kfoot-copy">{t.foot_copy}</p>
      </footer>
    </div>
  );
}
