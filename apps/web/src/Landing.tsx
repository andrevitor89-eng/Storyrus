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
const IcGift = ({ className }: IconProps) => (<Svg className={className}><rect x="3.5" y="10" width="17" height="10.5" rx="1.6" /><path d="M3 10h18M12 10v10.5" /><path d="M12 10S9 5.5 7 6.5 8.5 10 12 10zM12 10s3-4.5 5-3.5S15.5 10 12 10z" /></Svg>);
const IcHeart = ({ className }: IconProps) => (<Svg className={className}><path d="M12 20s-7-4.4-9-8.5C1.6 8.3 3.3 5.5 6.3 5.5c1.9 0 3 1.1 3.7 2.2.7-1.1 1.8-2.2 3.7-2.2 3 0 4.7 2.8 3.3 6C19 15.6 12 20 12 20z" /></Svg>);
const IcHome = ({ className }: IconProps) => (<Svg className={className}><path d="M4 11l8-6 8 6M6 10v9h12v-9" /></Svg>);
const IcSparkle = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 3l1.6 5L19 9.6l-5 1.6L12 17l-1.6-5.8L5 9.6 10.4 8 12 3z" /></svg>);
const IcArrow = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 40 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 12h28M24 4l9 8-9 8" /></svg>);
const IcSun = ({ className }: IconProps) => (<Svg className={className}><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" /></Svg>);
const IcMoon = ({ className }: IconProps) => (<Svg className={className}><path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" /></Svg>);
const IcChevron = ({ className }: IconProps) => (<Svg className={className}><path d="M6 9l6 6 6-6" /></Svg>);
const IcShield = ({ className }: IconProps) => (<Svg className={className}><path d="M12 3l7 2.5V11c0 4.4-3 7.7-7 9-4-1.3-7-4.6-7-9V5.5L12 3z" /><path d="M9.2 12l2 2 3.6-3.8" /></Svg>);
const IcEye = ({ className }: IconProps) => (<Svg className={className}><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" /><circle cx="12" cy="12" r="2.6" /></Svg>);
const IcTruck = ({ className }: IconProps) => (<Svg className={className}><path d="M3 6.5h11v9H3zM14 9.5h4l3 3v3h-7z" /><circle cx="7" cy="18" r="1.6" /><circle cx="17.5" cy="18" r="1.6" /></Svg>);

const NAV_ICONS = [IcHome, IcBook, IcSparkle, IcGift, IcHeart];
const PROMISE_ICONS = [IcShield, IcGift, IcEye, IcTruck];

/* ------- exemplos reais em apps/web/public/exemplos/ ------- */
const HOW_IMGS = ["foto-menino.jpg", "arte-menino.jpg", "livro-1.jpg"];
const BOOK = ["livro-1.jpg", "livro-2.jpg", "livro-3.jpg", "livro-4.jpg", "livro-5.jpg"];
const CATALOG_IMGS = ["tema-oceano.jpg", "tema-floresta.jpg", "tema-dino.jpg", "tema-circo.jpg"];
const CATALOG_THEMES = ["underwater", "fantasy", "dinosaurs", "adventure"];
const SURPRISE_IMG = "tema-surpresa.jpg";
const BANNER_IMGS = ["livro-3.jpg", "livro-2.jpg", "livro-4.jpg"];
const BA_PAIRS = [
  ["foto-bebe.jpg", "arte-bebe.jpg"],
  ["foto-menina.jpg", "arte-menina.jpg"],
  ["foto-bebe2.jpg", "arte-bebe2.jpg"],
  ["foto-menino.jpg", "arte-menino.jpg"],
  ["foto-pai.jpg", "arte-pai.jpg"],
];
const exUrl = (f: string) => `${import.meta.env.BASE_URL}exemplos/${f}`;

function Faq({ items }: { items: readonly { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="faq">
      {items.map((it, i) => (
        <div className={`faq-item${open === i ? " open" : ""}`} key={it.q}>
          <button className="faq-q" onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}>
            <span>{it.q}</span><IcChevron className="faq-chev" />
          </button>
          <div className="faq-a"><p>{it.a}</p></div>
        </div>
      ))}
    </div>
  );
}

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
    nav: ["Início", "Livros", "Como funciona", "Avaliações", "Perguntas"],
    explore: "Explorar agora",
    eyebrow: "Sua foto vira uma história",
    h_pre: "Transforme uma foto em uma ", w1: "história", c1: " onde seu filho é o ", w2: "herói", h_suf: ".",
    lead: "Você envia a foto e a gente cria um personagem ilustrado, uma história personalizada, um livro em PDF e até um vídeo narrado.",
    cta_play: "Criar minha história", cta_disc: "Ver como funciona",
    trust: "Encantando famílias do início ao fim",
    ba_before: "ANTES", ba_after: "DEPOIS", ba_caption: "Você envia a foto. A gente cria o encanto.",
    ba_title: "Antes e depois de verdade",
    ba_sub: "Fotos reais transformadas em personagens ilustrados.",
    ba_pairs: ["Do berço para a aventura", "Uma menina cheia de imaginação", "Sorriso que vira personagem", "Da foto ao herói da história", "Todo mundo pode ser protagonista"],
    banners: [
      { t: "Voe com a imaginação", p: "Cada página abre uma aventura nova onde seu filho é o protagonista." },
      { t: "Construa a própria história", p: "Escolha a aventura, personalize os detalhes e crie um livro único." },
      { t: "Explore mundos incríveis", p: "Aventuras que despertam a curiosidade e alimentam a imaginação." },
    ],
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
    cat_title: "Escolha um livro", cat_sub: "Cada tema vira uma história ilustrada com seu filho como protagonista.",
    price: "a partir de R$ 49", price_note: "digital ou impresso", personalize: "Personalizar",
    catalog: [
      { t: "Fundo do Mar", p: "Uma aventura no oceano com amigos marinhos.", age: "3-6 anos", tag: "Coragem e amizade" },
      { t: "Floresta Encantada", p: "Bichinhos gentis e luzes mágicas de vaga-lume.", age: "3-6 anos", tag: "Gentileza e natureza" },
      { t: "Mundo dos Dinossauros", p: "Um vale cheio de dinossauros dóceis.", age: "4-7 anos", tag: "Descoberta e curiosidade" },
      { t: "Circo das Luzes", p: "Uma noite mágica cheia de brilho.", age: "3-6 anos", tag: "Sonhar e brilhar" },
    ],
    surprise: { t: "História Surpresa (IA)", p: "Deixe a IA inventar uma aventura única a partir da foto.", age: "3-8 anos", tag: "Aventura sob medida" },
    promise_title: "Cada detalhe pensado para ser especial",
    promise_sub: "Do envio da foto à entrega, tudo é feito para o livro chegar pronto para presentear.",
    promise: [
      { t: "Privacidade da foto", p: "A imagem é usada só para preparar o livro do seu filho — nunca para divulgação." },
      { t: "Impressão pensada como presente", p: "Preparado para ficar lindo em mãos, na leitura em família e na hora de entregar." },
      { t: "Prévia antes de avançar", p: "Você vê a capa e as páginas e entende o que está criando antes de finalizar." },
      { t: "Entrega sem complicação", p: "Acompanhamos da personalização ao envio para tudo chegar prontinho." },
    ],
    faq_title: "Perguntas frequentes", faq_sub: "Tudo o que você precisa saber.",
    faq: [
      { q: "Como crio um livro personalizado?", a: "Escolha um tema, envie uma foto da criança e adicione o nome e uma dedicatória. A IA transforma a foto em ilustrações e você vê a prévia antes de finalizar." },
      { q: "Posso ver o livro antes?", a: "Sim! Você recebe uma prévia completa (capa e páginas) antes de baixar ou pedir a impressão." },
      { q: "A foto e os dados da criança estão seguros?", a: "Sim. Usamos a foto apenas para criar o livro e não compartilhamos seus dados." },
      { q: "Recebo digital ou impresso?", a: "Os dois: o e-book digital na hora e, se quiser, o livro impresso enviado até você." },
      { q: "Posso pedir alterações?", a: "Pode! Ajuste o nome, a dedicatória e regenere as ilustrações na prévia até ficar do seu jeito." },
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
    nav: ["Home", "Books", "How it works", "Reviews", "FAQ"],
    explore: "Explore now",
    eyebrow: "Your photo becomes a story",
    h_pre: "Turn a photo into a ", w1: "story", c1: " where your child is the ", w2: "hero", h_suf: ".",
    lead: "You send the photo and we create an illustrated character, a personalized story, a PDF book and even a narrated video.",
    cta_play: "Create my story", cta_disc: "See how it works",
    trust: "Delighting families from start to finish",
    ba_before: "BEFORE", ba_after: "AFTER", ba_caption: "You send the photo. We create the magic.",
    ba_title: "Real before and after",
    ba_sub: "Real photos turned into illustrated characters.",
    ba_pairs: ["From crib to adventure", "A girl full of imagination", "A smile that becomes a character", "From photo to story hero", "Anyone can be the hero"],
    banners: [
      { t: "Fly with imagination", p: "Every page opens a new adventure where your child is the hero." },
      { t: "Build their own story", p: "Choose the adventure, personalize the details and create a unique book." },
      { t: "Explore amazing worlds", p: "Adventures that spark curiosity and feed the imagination." },
    ],
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
    cat_title: "Choose a book", cat_sub: "Each theme becomes an illustrated story with your child as the hero.",
    price: "from $29", price_note: "digital or printed", personalize: "Personalize",
    catalog: [
      { t: "Deep Sea", p: "An ocean adventure with sea friends.", age: "ages 3-6", tag: "Courage & friendship" },
      { t: "Enchanted Forest", p: "Gentle creatures and magical firefly lights.", age: "ages 3-6", tag: "Kindness & nature" },
      { t: "Dinosaur World", p: "A valley full of gentle dinosaurs.", age: "ages 4-7", tag: "Discovery & curiosity" },
      { t: "Circus of Lights", p: "A magical night full of sparkle.", age: "ages 3-6", tag: "Dream & shine" },
    ],
    surprise: { t: "Surprise Story (AI)", p: "Let the AI invent a unique adventure from the photo.", age: "ages 3-8", tag: "Made-to-fit adventure" },
    promise_title: "Every detail crafted to feel special",
    promise_sub: "From the photo to delivery, everything is made so the book arrives ready to gift.",
    promise: [
      { t: "Photo privacy", p: "The image is used only to prepare your child's book — never for promotion." },
      { t: "Print made as a gift", p: "Prepared to look beautiful in hand, in shared reading and at the moment you give it." },
      { t: "Preview before you continue", p: "You see the cover and pages and understand what you're creating before finishing." },
      { t: "Hassle-free delivery", p: "We follow from personalization to shipping so everything arrives ready." },
    ],
    faq_title: "Frequently asked questions", faq_sub: "Everything you need to know.",
    faq: [
      { q: "How do I create a personalized book?", a: "Pick a theme, upload a photo of your child and add the name and a dedication. The AI turns the photo into illustrations and you see a preview before finishing." },
      { q: "Can I see the book before?", a: "Yes! You get a full preview (cover and pages) before downloading or ordering the print." },
      { q: "Are my child's photo and data safe?", a: "Yes. We use the photo only to create the book and never share your data." },
      { q: "Digital or printed?", a: "Both: the digital e-book right away and, if you want, the printed book shipped to you." },
      { q: "Can I request changes?", a: "You can! Adjust the name, the dedication and regenerate the illustrations in the preview." },
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
  const t = I18N[lang];
  const navHrefs = ["#top", "#catalogo", "#como", "#reviews", "#faq"];
  const featIcons = [IcSparkle, IcHeart, IcBook, IcGift];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);

  useEffect(() => {
    const els = rootRef.current?.querySelectorAll(".reveal") ?? [];
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    els.forEach((el, i) => { (el as HTMLElement).style.transitionDelay = `${(i % 3) * 0.1}s`; io.observe(el); });
    return () => io.disconnect();
  }, []);

  const closeNav = () => setNavOpen(false);

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
          <div className="beforeafter">
            <figure className="ba-side">
              <img src={exUrl("foto-bebe.jpg")} alt="Foto real" loading="eager" />
              <span className="ba-tag tag-before">{t.ba_before}</span>
            </figure>
            <span className="ba-arrow" aria-hidden><IcArrow /></span>
            <figure className="ba-side">
              <img src={exUrl("arte-bebe.jpg")} alt="Ilustração criada" loading="eager" />
              <span className="ba-tag tag-after">{t.ba_after}</span>
            </figure>
          </div>
          <div className="ba-caption"><IcHeart className="ci" /> {t.ba_caption}</div>
        </div>
      </section>

      {/* BANNERS NARRATIVOS */}
      <section className="banners">
        {t.banners.map((b, i) => (
          <figure className="banner-card reveal" key={b.t}>
            <img src={exUrl(BANNER_IMGS[i])} alt={b.t} loading="lazy" />
            <figcaption><h3>{b.t}</h3><p>{b.p}</p></figcaption>
          </figure>
        ))}
      </section>

      {/* GALERIA ANTES E DEPOIS */}
      <section className="ksection" id="antes-depois">
        <h2 className="ktitle reveal">{t.ba_title}</h2>
        <p className="ksub reveal">{t.ba_sub}</p>
        <div className="ba-gallery">
          {BA_PAIRS.map((pair, i) => (
            <div className="bapair reveal" key={pair[0]}>
              <div className="bapair-imgs">
                <figure className="bap-side">
                  <img src={exUrl(pair[0])} alt="Foto real" loading="lazy" />
                  <span className="ba-tag tag-before">{t.ba_before}</span>
                </figure>
                <span className="bap-arrow" aria-hidden><IcArrow /></span>
                <figure className="bap-side">
                  <img src={exUrl(pair[1])} alt="Ilustração criada" loading="lazy" />
                  <span className="ba-tag tag-after">{t.ba_after}</span>
                </figure>
              </div>
              <p className="bapair-cap"><IcHeart className="ci" /> {t.ba_pairs[i]}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CATÁLOGO DE LIVROS */}
      <section className="ksection" id="catalogo">
        <h2 className="ktitle reveal">{t.cat_title}</h2>
        <p className="ksub reveal">{t.cat_sub}</p>
        <div className="cat-grid">
          {t.catalog.map((c, i) => (
            <div className="cat-card reveal" key={c.t}>
              <div className="cat-cover">
                <img src={exUrl(CATALOG_IMGS[i])} alt={c.t} loading="lazy" />
                <span className="cat-off">-33%</span>
              </div>
              <div className="cat-body">
                <div className="cat-badges"><span className="cat-age">{c.age}</span><span className="cat-tag">{c.tag}</span></div>
                <h3>{c.t}</h3>
                <p>{c.p}</p>
                <div className="cat-price">{t.price}<span>· {t.price_note}</span></div>
                <Link to={`/app?tema=${CATALOG_THEMES[i]}`} className="kbtn kbtn-primary">{t.personalize}</Link>
              </div>
            </div>
          ))}
          <div className="cat-card surprise reveal">
            <div className="cat-cover">
              <img src={exUrl(SURPRISE_IMG)} alt={t.surprise.t} loading="lazy" />
              <span className="cat-ia"><IcSparkle /></span>
            </div>
            <div className="cat-body">
              <div className="cat-badges"><span className="cat-age">{t.surprise.age}</span><span className="cat-tag">{t.surprise.tag}</span></div>
              <h3>{t.surprise.t}</h3>
              <p>{t.surprise.p}</p>
              <div className="cat-price">{t.price}<span>· {t.price_note}</span></div>
              <Link to="/app" className="kbtn kbtn-soft">{t.personalize}</Link>
            </div>
          </div>
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

      {/* NOSSA PROMESSA */}
      <section className="ksection" id="promessa">
        <h2 className="ktitle reveal">{t.promise_title}</h2>
        <p className="ksub reveal">{t.promise_sub}</p>
        <div className="promise-grid">
          {t.promise.map((pr, i) => {
            const Icon = PROMISE_ICONS[i];
            return (
              <div className="promise-card reveal" key={pr.t}>
                <span className="promise-ic"><Icon /></span>
                <h3>{pr.t}</h3>
                <p>{pr.p}</p>
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

      {/* FAQ */}
      <section className="ksection" id="faq">
        <h2 className="ktitle reveal">{t.faq_title}</h2>
        <p className="ksub reveal">{t.faq_sub}</p>
        <div className="reveal"><Faq items={t.faq} /></div>
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
