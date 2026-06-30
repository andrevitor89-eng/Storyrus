import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

type Lang = "pt" | "en";

const ICONS = {
  nav: ["🏡", "📖", "🎨", "⭐", "💞"],
  steps: ["📷", "🎨", "🖌️", "📖", "🎬", "🎁"],
  areas: ["🏠", "🎨", "🎮", "📚", "⭐"],
  area_c: ["a1", "a2", "a3", "a4", "a5"],
  family: ["🔒", "💛", "🤝"],
};

const I18N = {
  pt: {
    nav: ["Início", "Histórias", "Criatividade", "Novidades", "Para famílias"],
    explore: "🚀 Explorar agora",
    eyebrow: "✨ Histórias encantadas com IA",
    h_pre: "Um mundo de ", w1: "histórias", c1: ", ", w2: "descobertas", c2: " e ",
    w3: "aventuras", h_suf: " começa aqui!",
    lead: "Envie uma foto e veja a criança virar o herói da própria história — em e-books ilustrados e vídeos cheios de imaginação.",
    cta_play: "🎈 Vamos brincar", cta_disc: "📖 Descobrir histórias",
    trust: "Encantando famílias do início ao fim",
    steps_title: "Da foto ao encanto ✨", steps_sub: "Simples para você. Encantador no resultado.",
    steps: [
      { t: "Envie uma foto", p: "É só uma foto para a magia começar." },
      { t: "Escolha a aventura", p: "Aventura, princesas, espaço, dinossauros e muito mais." },
      { t: "A IA cria a arte", p: "Seu herói ganha vida em ilustrações encantadas." },
      { t: "Receba o e-book", p: "Um livro só seu, do começo ao fim." },
      { t: "Ganhe o vídeo", p: "A história narrada para emocionar a família." },
      { t: "Lembrança única", p: "Feita para guardar para sempre." },
    ],
    play_title: "Explore e descubra 🗺️", play_sub: "Toque nas áreas para desbloquear aventuras!",
    reward_start: "Comece a explorar para ganhar estrelas!",
    reward_some: (n: number) => `Você encontrou ${n} aventura${n > 1 ? "s" : ""}!`,
    reward_all: "🏅 Incrível! Você desbloqueou todas as aventuras!",
    areas: [
      { title: "Casa das histórias", desc: "Onde toda aventura começa." },
      { title: "Área criativa", desc: "Crie, pinte e invente." },
      { title: "Jogos", desc: "Brincadeiras para explorar." },
      { title: "Biblioteca", desc: "Seus livros encantados." },
      { title: "Desafios", desc: "Conquiste estrelas e medalhas." },
    ],
    badge_tap: "tocar", badge_done: "⭐ descoberto",
    band_title: "Pronto para virar protagonista?",
    band_sub: "Envie sua foto e receba uma história única, criada só para você.",
    band_cta: "✨ Criar minha história",
    fam_title: "Para as famílias 💞", fam_sub: "Diversão para as crianças, tranquilidade para você.",
    family: [
      { t: "Seguro", p: "Ambiente protegido, sem anúncios e pensado para crianças." },
      { t: "Feito com carinho", p: "Conteúdo gentil, positivo e adequado à idade." },
      { t: "Para toda a família", p: "Momentos para criar e ler juntos." },
    ],
    foot_tag: "Toda criança merece ver a própria história ganhar vida. 💛",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  en: {
    nav: ["Home", "Stories", "Creativity", "What's new", "For families"],
    explore: "🚀 Explore now",
    eyebrow: "✨ Enchanting AI stories",
    h_pre: "A world of ", w1: "stories", c1: ", ", w2: "discoveries", c2: " and ",
    w3: "adventures", h_suf: " begins here!",
    lead: "Send a photo and watch your child become the hero of their own story — in illustrated e-books and videos full of imagination.",
    cta_play: "🎈 Let's play", cta_disc: "📖 Discover stories",
    trust: "Delighting families from start to finish",
    steps_title: "From photo to wonder ✨", steps_sub: "Simple for you. Wonderful in the result.",
    steps: [
      { t: "Send a photo", p: "One photo is all it takes for the magic to begin." },
      { t: "Pick the adventure", p: "Adventure, princesses, space, dinosaurs and more." },
      { t: "AI creates the art", p: "Your hero comes to life in enchanting illustrations." },
      { t: "Get the e-book", p: "A book that's all yours, start to finish." },
      { t: "Receive the video", p: "The narrated story to move the whole family." },
      { t: "A unique keepsake", p: "Made to be kept forever." },
    ],
    play_title: "Explore and discover 🗺️", play_sub: "Tap the areas to unlock adventures!",
    reward_start: "Start exploring to earn stars!",
    reward_some: (n: number) => `You found ${n} adventure${n > 1 ? "s" : ""}!`,
    reward_all: "🏅 Amazing! You unlocked all the adventures!",
    areas: [
      { title: "Story house", desc: "Where every adventure begins." },
      { title: "Creative zone", desc: "Create, paint and invent." },
      { title: "Games", desc: "Playful ways to explore." },
      { title: "Library", desc: "Your enchanted books." },
      { title: "Challenges", desc: "Earn stars and medals." },
    ],
    badge_tap: "tap", badge_done: "⭐ found",
    band_title: "Ready to become the hero?",
    band_sub: "Send your photo and get a unique story, made just for you.",
    band_cta: "✨ Create my story",
    fam_title: "For families 👨‍👩‍👧", fam_sub: "Fun for kids, peace of mind for you.",
    family: [
      { t: "Safe", p: "A protected, ad-free space designed for children." },
      { t: "Made with care", p: "Gentle, positive and age-appropriate content." },
      { t: "For the whole family", p: "Moments to create and read together." },
    ],
    foot_tag: "Every child deserves to see their story come to life. 💛",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
} as const;

export function Landing() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [found, setFound] = useState<number[]>([]);
  const [lang, setLang] = useState<Lang>("pt");
  const t = I18N[lang];
  const navHrefs = ["#top", "#historias", "#criatividade", "#novidades", "#familias"];

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
      (el as HTMLElement).style.transitionDelay = `${(i % 4) * 0.08}s`;
      io.observe(el);
    });
    return () => io.disconnect();
  }, []);

  const discover = (i: number) => setFound((f) => (f.includes(i) ? f : [...f, i]));
  const closeNav = () => setNavOpen(false);

  return (
    <div className="kid" ref={rootRef} id="top">
      <div className="sky" aria-hidden>
        <span className="cloud c1">☁️</span>
        <span className="cloud c2">☁️</span>
        <span className="cloud c3">☁️</span>
        <span className="twk t1">✦</span>
        <span className="twk t2">✧</span>
        <span className="twk t3">★</span>
        <span className="twk t4">✦</span>
      </div>

      <header className="knav">
        <a href="#top" className="kbrand"><img src={logo} alt="Story.R.Us" /></a>
        <nav className={`klinks${navOpen ? " open" : ""}`}>
          {t.nav.map((label, i) => (
            <a key={label} href={navHrefs[i]} onClick={closeNav}>
              <span className="ni">{ICONS.nav[i]}</span>
              {label}
            </a>
          ))}
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

      <section className="khero">
        <div className="khero-text">
          <span className="keyebrow">{t.eyebrow}</span>
          <h1>
            {t.h_pre}<span className="g1">{t.w1}</span>{t.c1}<span className="g2">{t.w2}</span>
            {t.c2}<span className="g3">{t.w3}</span>{t.h_suf}
          </h1>
          <p className="klead">{t.lead}</p>
          <div className="khero-cta">
            <Link to="/app" className="kbtn kbtn-primary">{t.cta_play}</Link>
            <a href="#historias" className="kbtn kbtn-soft">{t.cta_disc}</a>
          </div>
          <div className="ktrust"><span className="stars">★★★★★</span> {t.trust}</div>
        </div>

        <div className="khero-art">
          <div className="mascot-wrap">
            <svg className="mascot" viewBox="0 0 220 240" xmlns="http://www.w3.org/2000/svg" aria-label="Mascote">
              <ellipse cx="110" cy="225" rx="60" ry="10" fill="rgba(0,0,0,.08)" />
              <path d="M40 120 C40 55 180 55 180 120 C180 185 150 210 110 210 C70 210 40 185 40 120 Z" fill="#ffd23f"/>
              <circle cx="60" cy="92" r="10" fill="#ff8a5c"/>
              <circle cx="160" cy="92" r="10" fill="#ff8a5c"/>
              <circle cx="88" cy="110" r="16" fill="#fff"/>
              <circle cx="132" cy="110" r="16" fill="#fff"/>
              <circle cx="92" cy="113" r="7" fill="#2f2a44"/>
              <circle cx="128" cy="113" r="7" fill="#2f2a44"/>
              <circle cx="94" cy="111" r="2.4" fill="#fff"/>
              <circle cx="130" cy="111" r="2.4" fill="#fff"/>
              <path d="M92 145 Q110 165 128 145" stroke="#b5552e" strokeWidth="6" fill="none" strokeLinecap="round"/>
              <path d="M110 40 L118 60 L100 60 Z" fill="#ff5d8f"/>
              <circle cx="110" cy="34" r="7" fill="#7c5cff"/>
            </svg>
            <span className="floaty f1">⭐</span>
            <span className="floaty f2">🚀</span>
            <span className="floaty f3">🎈</span>
            <span className="floaty f4">🌈</span>
          </div>
        </div>
      </section>

      <section className="ksection" id="historias">
        <h2 className="ktitle reveal">{t.steps_title}</h2>
        <p className="ksub reveal">{t.steps_sub}</p>
        <div className="kgrid steps">
          {t.steps.map((s, i) => (
            <div className="kcard reveal" key={s.t}>
              <div className="kemoji">{ICONS.steps[i]}</div>
              <h3>{s.t}</h3>
              <p>{s.p}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="ksection play" id="criatividade">
        <h2 className="ktitle reveal">{t.play_title}</h2>
        <p className="ksub reveal">{t.play_sub}</p>

        <div className="reward reveal">
          <span className="rstars">{"★".repeat(found.length)}{"☆".repeat(5 - found.length)}</span>
          <b>
            {found.length === 0 && t.reward_start}
            {found.length > 0 && found.length < 5 && t.reward_some(found.length)}
            {found.length === 5 && t.reward_all}
          </b>
        </div>

        <div className="kgrid areas">
          {t.areas.map((a, i) => (
            <button
              key={a.title}
              className={`area ${ICONS.area_c[i]} reveal ${found.includes(i) ? "done" : ""}`}
              onClick={() => discover(i)}
            >
              <span className="aemoji">{ICONS.areas[i]}</span>
              <h3>{a.title}</h3>
              <p>{a.desc}</p>
              <span className="badge">{found.includes(i) ? t.badge_done : t.badge_tap}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="kband" id="novidades">
        <span className="twk b1">✦</span>
        <span className="twk b2">✧</span>
        <h2>{t.band_title}</h2>
        <p>{t.band_sub}</p>
        <Link to="/app" className="kbtn kbtn-primary big">{t.band_cta}</Link>
      </section>

      <section className="ksection" id="familias">
        <h2 className="ktitle reveal">{t.fam_title}</h2>
        <p className="ksub reveal">{t.fam_sub}</p>
        <div className="kgrid family">
          {t.family.map((f, i) => (
            <div className="kcard soft reveal" key={f.t}>
              <div className="kemoji">{ICONS.family[i]}</div>
              <h3>{f.t}</h3>
              <p>{f.p}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="kfoot">
        <div className="kfoot-nav">
          {t.nav.map((label, i) => (
            <a key={label} href={navHrefs[i]}><span>{ICONS.nav[i]}</span>{label}</a>
          ))}
        </div>
        <p className="kfoot-tag">{t.foot_tag}</p>
        <p className="kfoot-copy">{t.foot_copy}</p>
      </footer>
    </div>
  );
}
