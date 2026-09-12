import { Fragment, useEffect, useRef, useState, type KeyboardEvent as RKeyboardEvent, type MouseEvent as RMouseEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import logo from "./assets/logo.png";
import "./landing.css";

type Lang = "pt" | "en" | "es";

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
const IcSparkle = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 3l1.6 5L19 9.6l-5 1.6L12 17l-1.6-5.8L5 9.6 10.4 8 12 3z" /></svg>);
const IcArrow = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 40 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 12h28M24 4l9 8-9 8" /></svg>);
const IcSun = ({ className }: IconProps) => (<Svg className={className}><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" /></Svg>);
const IcMoon = ({ className }: IconProps) => (<Svg className={className}><path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" /></Svg>);
const IcChevron = ({ className }: IconProps) => (<Svg className={className}><path d="M6 9l6 6 6-6" /></Svg>);
const IcShield = ({ className }: IconProps) => (<Svg className={className}><path d="M12 3l7 2.5V11c0 4.4-3 7.7-7 9-4-1.3-7-4.6-7-9V5.5L12 3z" /><path d="M9.2 12l2 2 3.6-3.8" /></Svg>);
const IcEye = ({ className }: IconProps) => (<Svg className={className}><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" /><circle cx="12" cy="12" r="2.6" /></Svg>);
const IcTruck = ({ className }: IconProps) => (<Svg className={className}><path d="M3 6.5h11v9H3zM14 9.5h4l3 3v3h-7z" /><circle cx="7" cy="18" r="1.6" /><circle cx="17.5" cy="18" r="1.6" /></Svg>);
const IcPlay = ({ className }: IconProps) => (<Svg className={className}><rect x="3" y="5.5" width="18" height="13" rx="2.5" /><path d="M10 9.5l4.5 2.5-4.5 2.5z" fill="currentColor" stroke="none" /></Svg>);
const IcCheck = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M4 12.5l5 5L20 6.5" /></svg>);
const IcClose = ({ className }: IconProps) => (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M6 6l12 12M18 6L6 18" /></svg>);
const IcMail = ({ className }: IconProps) => (
  <Svg className={className}><rect x="3" y="5.5" width="18" height="13" rx="2" /><path d="M3.5 7.5 12 13l8.5-5.5" /></Svg>
);
const IcInstagram = ({ className }: IconProps) => (
  <Svg className={className}>
    <rect x="3.5" y="3.5" width="17" height="17" rx="5" />
    <circle cx="12" cy="12" r="4" />
    <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none" />
  </Svg>
);

const FOOT_ICONS = [IcSparkle, IcBook, IcPlay, IcStar];
const CONTACT_EMAIL = "Storyrus@outlook.com";
const CONTACT_INSTA = "storyrusbr";
const PROMISE_ICONS = [IcShield, IcGift, IcEye, IcTruck];
const FLIP_MS = 600;
const FLIP_AUTO_MS = 2000;

type CoverFont = "fredoka" | "baloo" | "lilita";

/* ------- exemplos reais em apps/web/public/exemplos/ ------- */
const HOW_IMGS = ["dica-boa.png", "personagem-avatar.jpg", "cena-dino-floresta.jpg"];
// Dicas de enquadramento: 1 exemplo bom (verde) + 2 a evitar (X).
// img = foto real local (public/exemplos/) ou URL externa; art = ilustração SVG de fallback.
const SHOTS: { img?: string; art?: "good" | "multi" | "side" | "covered"; ok: boolean; focus?: string }[] = [
  { img: "dica-boa.png", ok: true, focus: "center center" },
  { img: "dica-multi.png", ok: false, focus: "68% 38%" },
  { img: "dica-lado.png", ok: false, focus: "78% 32%" },
];
/** Hero FlipBook: only lifestyle books (child holding the book) from landing/ */
const HERO_BOOKS = [
  { tab: "foto-martin-goleiro.jpg", cover: "capa-martin-goleiro.jpg", page: "pagina-martin-goleiro.jpg" },
  { tab: "foto-emilia-bailarina.jpg", cover: "capa-emilia-bailarina.jpg", page: "pagina-emilia-bailarina.jpg" },
  { tab: "foto-antonio-bicicleta.jpg", cover: "capa-antonio-bicicleta.jpg", page: "pagina-antonio-bicicleta.jpg" },
  { tab: "foto-mariajesus-hockey.jpg", cover: "capa-mariajesus-hockey.jpg", page: "pagina-mariajesus-hockey.jpg" },
  { tab: "foto-facundo-motocross.jpg", cover: "capa-facundo-motocross.jpg", page: "pagina-facundo-motocross.jpg" },
] as const;
const CATALOG_IMGS = [
  "capa-martin-goleiro.jpg",
  "capa-emilia-bailarina.jpg",
  "capa-antonio-bicicleta.jpg",
  "capa-sofia-alfabeto.jpg",
  "capa-bruno-animais.jpg",
  "capa-cristobal-esporte.jpg",
];
const CATALOG_THEMES = [
  "adventure",
  "princess",
  "adventure",
  "alfabetizacao_inicial",
  "animais_sons",
  "adventure",
];
const BOOK3D = [
  { bg: "#efe4c4" },
  { bg: "#e4eed4" },
  { bg: "#d4e8f6" },
  { bg: "#f0e4f4" },
  { bg: "#e8f4e4" },
  { bg: "#e4eef8" },
];
const VIDEO_IMGS = ["mar-2.jpg", "flor-2.jpg", "dino-2.jpg"];
const VIDEO_SRCS: (string | null)[] = ["video-mar.mp4", "video-flor.mp4", "video-dino.mp4"];
const NAV_CAT_META = [
  {
    color: "#5aa6e8",
    subs: [
      { href: "/app?tema=adventure" },
      { href: "/app?tema=fantasy" },
      { href: "/app?tema=dinosaurs" },
      { href: "/app?tema=underwater" },
      { href: "/app?tema=space" },
      { href: "/app?tema=princess" },
      { href: "/app?tema=superhero" },
    ],
    feats: [
      { href: "/app?tema=alfabetizacao_inicial", img: "capa-martin-goleiro.jpg", catalogI: 0 },
      { href: "/app?tema=animais_sons", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
      { href: "/app?tema=adventure", img: "capa-antonio-bicicleta.jpg", catalogI: 2 },
      { href: "/app?tema=fantasy", img: "capa-martin-goleiro.jpg", catalogI: 0 },
    ],
  },
  {
    color: "#f0b429",
    subs: [
      { href: "/app?tema=christmas" },
      { href: "/app?tema=birthday" },
      { href: "/app?tema=mothers_day" },
      { href: "/app?tema=fathers_day" },
      { href: "/app?tema=easter" },
      { href: "/app?tema=childrens_day" },
      { href: "/app?tema=new_year" },
    ],
    feats: [
      { href: "/app?tema=christmas", img: "capa-martin-goleiro.jpg", catalogI: 0 },
      { href: "/app?tema=birthday", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
      { href: "/app?tema=mothers_day", img: "capa-antonio-bicicleta.jpg", catalogI: 2 },
      { href: "/app?tema=fathers_day", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
    ],
  },
  {
    color: "#b48ad4",
    subs: [
      { href: "/app?tema=mothers_day" },
      { href: "/app?tema=fathers_day" },
      { href: "/app" },
      { href: "/app" },
    ],
    feats: [
      { href: "/app?tema=mothers_day", img: "capa-martin-goleiro.jpg", catalogI: 0 },
      { href: "/app?tema=fathers_day", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
      { href: "/app", img: "capa-antonio-bicicleta.jpg", catalogI: 2 },
      { href: "/app", img: "capa-martin-goleiro.jpg", catalogI: 0 },
    ],
  },
  {
    color: "#f0a0c0",
    subs: [
      { href: "/app?tema=literacia_emocional" },
      { href: "/app?tema=rotina_dormir" },
      { href: "/app?tema=compartilhar_revezar" },
      { href: "/app?tema=consciencia_corporal" },
    ],
    feats: [
      { href: "/app?tema=literacia_emocional", img: "capa-martin-goleiro.jpg", catalogI: 0 },
      { href: "/app?tema=rotina_dormir", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
      { href: "/app?tema=compartilhar_revezar", img: "capa-antonio-bicicleta.jpg", catalogI: 2 },
      { href: "/app?tema=consciencia_corporal", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
    ],
  },
  {
    color: "#5ec4a8",
    subs: [
      { href: "/app?tema=alfabetizacao_inicial" },
      { href: "/app?tema=pensamento_matematico" },
      { href: "/app?tema=cores" },
      { href: "/app?tema=higiene_desfralde" },
      { href: "/app?tema=vestir_autonomia" },
      { href: "/app?tema=animais_sons" },
      { href: "/app?tema=transporte_ajudantes" },
    ],
    feats: [
      { href: "/app?tema=alfabetizacao_inicial", img: "capa-martin-goleiro.jpg", catalogI: 0 },
      { href: "/app?tema=pensamento_matematico", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
      { href: "/app?tema=cores", img: "capa-antonio-bicicleta.jpg", catalogI: 2 },
      { href: "/app?tema=animais_sons", img: "capa-emilia-bailarina.jpg", catalogI: 1 },
    ],
  },
] as const;
const exUrl = (f: string) => (f.startsWith("http://") || f.startsWith("https://") ? f : `${import.meta.env.BASE_URL}exemplos/${f}`);

/* Ilustrações das dicas de enquadramento (SVG inline, sem depender de fotos) */
function ShotArt({ kind }: { kind: "good" | "multi" | "side" | "covered" }) {
  const face = "#f4c19a", hair = "#6b4a2b", eye = "#3a2b1c", mouth = "#a15a3a";
  if (kind === "multi") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <g>
          <rect x="24" y="76" width="20" height="26" rx="10" fill="#8fb4dd" />
          <circle cx="34" cy="58" r="16" fill={face} /><path d="M19 57q0-18 15-18t15 18q0-9-15-9t-15 9Z" fill="#7a5230" />
          <circle cx="29" cy="57" r="2.1" fill={eye} /><circle cx="39" cy="57" r="2.1" fill={eye} /><path d="M29 63q5 4 10 0" stroke={mouth} strokeWidth="2" fill="none" strokeLinecap="round" />
        </g>
        <g>
          <rect x="76" y="76" width="20" height="26" rx="10" fill="#8ccdb0" />
          <circle cx="86" cy="58" r="16" fill={face} /><path d="M71 57q0-18 15-18t15 18q0-9-15-9t-15 9Z" fill={hair} />
          <circle cx="81" cy="57" r="2.1" fill={eye} /><circle cx="91" cy="57" r="2.1" fill={eye} /><path d="M81 63q5 4 10 0" stroke={mouth} strokeWidth="2" fill="none" strokeLinecap="round" />
        </g>
        <g>
          <rect x="47" y="72" width="26" height="34" rx="12" fill="#e79a9a" />
          <circle cx="60" cy="52" r="19" fill="#eab98f" /><path d="M41 51q0-21 19-21t19 21q0-10-19-10t-19 10Z" fill="#4a3320" />
          <circle cx="54" cy="51" r="2.4" fill={eye} /><circle cx="66" cy="51" r="2.4" fill={eye} /><path d="M54 58q6 5 12 0" stroke={mouth} strokeWidth="2.2" fill="none" strokeLinecap="round" />
        </g>
      </svg>
    );
  }
  if (kind === "side") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <rect x="50" y="88" width="16" height="18" rx="8" fill="#eeb086" />
        <circle cx="56" cy="60" r="28" fill={face} />
        <path d="M28 60q0-30 28-30 16 0 25 12l-12 3q-7-9-17-7-24 4-24 22Z" fill={hair} />
        <path d="M30 62q-3 14 10 20-8-16-2-28-5 2-8 8Z" fill={hair} />
        <circle cx="46" cy="63" r="4" fill="#eeb086" />
        <path d="M83 57q7 4 0 9" fill={face} stroke="#e2a880" strokeWidth="1.4" />
        <circle cx="71" cy="58" r="3.1" fill={eye} />
        <path d="M70 72q7 3 12 0" stroke={mouth} strokeWidth="2.6" fill="none" strokeLinecap="round" />
      </svg>
    );
  }
  if (kind === "covered") {
    return (
      <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <rect width="120" height="120" fill="#e7ecf4" />
        <rect x="52" y="88" width="16" height="18" rx="8" fill="#eeb086" />
        <circle cx="60" cy="60" r="30" fill={face} />
        <path d="M30 58q0-30 30-30t30 30q0-14-12-18-8-8-18-8t-18 8q-12 4-12 18Z" fill={hair} />
        <circle cx="50" cy="56" r="3.3" fill={eye} /><circle cx="70" cy="56" r="3.3" fill={eye} />
        <path d="M34 66q26-6 52 0l0 8q-26 18-52 0Z" fill="#7f9bc4" />
        <path d="M34 66l-6 4M86 66l6 4" stroke="#7f9bc4" strokeWidth="3" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg className="shot-svg" viewBox="0 0 120 120" preserveAspectRatio="xMidYMid slice" aria-hidden>
      <rect width="120" height="120" fill="#ffe0b0" />
      <circle cx="97" cy="23" r="15" fill="#fff2cf" opacity="0.85" />
      <rect x="52" y="86" width="16" height="18" rx="8" fill="#eeb086" />
      <circle cx="60" cy="62" r="30" fill={face} />
      <path d="M30 60q0-32 30-32t30 32q0-14-12-18-8-8-18-8t-18 8q-12 4-12 18Z" fill={hair} />
      <circle cx="50" cy="60" r="3.4" fill={eye} /><circle cx="70" cy="60" r="3.4" fill={eye} />
      <circle cx="46" cy="70" r="4" fill="#f2a982" opacity=".6" /><circle cx="74" cy="70" r="4" fill="#f2a982" opacity=".6" />
      <path d="M49 74q11 10 22 0" stroke={mouth} strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  );
}

/** Vídeo de exemplo: carrega e toca só quando entra na tela. */
function AutoMutedVideo({ src, poster }: { src: string; poster: string }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [activeSrc, setActiveSrc] = useState<string | undefined>(undefined);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.muted = true;
    el.defaultMuted = true;
    const tryPlay = () => {
      el.muted = true;
      void el.play().catch(() => { /* autoplay bloqueado até interação */ });
    };
    const io = new IntersectionObserver(
      (entries) => {
        for (const en of entries) {
          if (en.isIntersecting) {
            setActiveSrc(src);
            tryPlay();
          } else {
            el.pause();
          }
        }
      },
      { threshold: 0.25 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [src]);
  useEffect(() => {
    const el = ref.current;
    if (!el || !activeSrc) return;
    el.muted = true;
    void el.play().catch(() => { /* autoplay bloqueado até interação */ });
  }, [activeSrc]);
  return (
    <video
      ref={ref}
      poster={poster}
      controls
      muted
      playsInline
      preload="metadata"
      loop
    >
      {activeSrc ? <source src={activeSrc} type="video/mp4" /> : null}
    </video>
  );
}

function Faq({ items }: { items: readonly { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="faq">
      {items.map((it, i) => {
        const qid = `faq-q-${i}`;
        const aid = `faq-a-${i}`;
        return (
        <div className={`faq-item${open === i ? " open" : ""}`} key={it.q}>
          <button
            type="button"
            className="faq-q"
            id={qid}
            onClick={() => setOpen(open === i ? null : i)}
            aria-expanded={open === i}
            aria-controls={aid}
          >
            <span>{it.q}</span><IcChevron className="faq-chev" />
          </button>
          <div className="faq-a" id={aid} role="region" aria-labelledby={qid} aria-hidden={open !== i}>
            <div className="faq-a-inner">
              <p>{it.a}</p>
            </div>
          </div>
        </div>
        );
      })}
    </div>
  );
}

function FlipBook({
  pages,
  compact = false,
  labels,
}: {
  pages: string[];
  compact?: boolean;
  labels?: { prev: string; next: string; turn: string; cover: string };
}) {
  const [i, setI] = useState(0);
  const [anim, setAnim] = useState<"next" | "prev" | null>(null);
  const [target, setTarget] = useState(0);
  const [hover, setHover] = useState(false);
  const busy = useRef(false);
  const flip = (dir: "next" | "prev", loop = false) => {
    if (busy.current || pages.length < 2) return;
    let t = dir === "next" ? i + 1 : i - 1;
    if (t >= pages.length) { if (!loop) return; t = 0; }
    if (t < 0) return;
    busy.current = true;
    setTarget(t);
    setAnim(dir);
    window.setTimeout(() => {
      setI(t);
      setAnim(null);
      busy.current = false;
    }, FLIP_MS);
  };
  useEffect(() => {
    if (!hover) return;
    const id = window.setTimeout(() => flip("next", true), FLIP_AUTO_MS);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [i, pages.length, hover]);
  useEffect(() => {
    if (hover) return;
    busy.current = false;
    setAnim(null);
    setI(0);
    setTarget(0);
  }, [hover]);
  const underSrc = anim === "next" ? pages[target] : pages[i];
  const leafSrc = anim === "next" ? pages[i] : (anim === "prev" ? pages[target] : pages[i]);
  const underIdx = anim === "next" ? target : i;
  const leafIdx = anim === "next" ? i : (anim === "prev" ? target : i);
  const pageKind = (idx: number) => (idx === 0 ? "fb-page--cover" : "fb-page--spread");
  const L = labels ?? { prev: "Página anterior", next: "Próxima página", turn: "Virar página", cover: "Capa" };
  const onStage = (e: RMouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (e.clientX - r.left > r.width / 2) flip("next", true); else flip("prev");
  };
  const onStageKey = (e: RKeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") {
      e.preventDefault();
      flip("next", true);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      flip("prev");
    }
  };
  return (
    <div
      className={`flipbook${compact ? " flipbook-mini" : ""}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {!compact && <button className="fb-nav" onClick={() => flip("prev")} disabled={i === 0 || !!anim} aria-label={L.prev}>‹</button>}
      <div className="fb-stage" onClick={onStage} onKeyDown={onStageKey} role="button" tabIndex={0} aria-label={L.turn}>
        <span className="fb-spine" />
        <img className={`fb-page fb-under ${pageKind(underIdx)}`} src={exUrl(underSrc)} alt="" aria-hidden />
        <div className={`fb-leaf${anim ? ` ${anim}` : ""}`}>
          <img className={`fb-page ${pageKind(leafIdx)}`} src={exUrl(leafSrc)} alt={i === 0 ? L.cover : `${i} / ${pages.length - 1}`} />
          <span className="fb-leaf-shade" aria-hidden />
        </div>
        <span className="fb-count">{i === 0 ? L.cover : `${i} / ${pages.length - 1}`}</span>
      </div>
      {!compact && <button className="fb-nav" onClick={() => flip("next")} disabled={i === pages.length - 1 || !!anim} aria-label={L.next}>›</button>}
    </div>
  );
}

const I18N = {
  pt: {
    nav: ["Como funciona", "Livros", "Vídeos", "FAQ"],
    reviews_link: "Avaliações",
    my_books: "Meus Livros",
    our_story: "Personalização",
    see_all_books: "Ver todos os livros",
    view_all: "Ver todos",
    cats_label: "Categorias",
    font_label: "Fonte do título",
    explore: "Explorar agora",
    eyebrow: "Eternize momentos. Presenteie familiares com uma história inesquecível.",
    h_pre: "Transforme uma foto em uma ", w1: "história inesquecível", c1: ", onde seu filho é o ", w2: "protagonista", h_suf: " !",
    lead: "Você envia a foto e nós transformamos seu pequeno em um personagem ilustrado, criando uma aventura personalizada especialmente para ele — um livro para presentear a família e guardar para sempre.",
    cta_play: "Criar minha conta",
    hero_cta: "Criar meu livro",
    cta_story: "Criar minha história",
    hero_sign: "Uma foto. Uma história. Uma memória eterna.",
    cats: [
      {
        name: "Aventuras Favoritas",
        subs: ["Aventura", "Fantasia", "Dinossauros", "Fundo do mar", "Espaço", "Princesas", "Super-heróis"],
        feats: ["Aprendendo o Alfabeto com a Sofia", "Bruno em uma aventura animal", "Cristobal e seu Esporte Favorito", "Aprendendo o Alfabeto com a Sofia"],
      },
      {
        name: "Ocasiões Especiais",
        subs: ["Natal", "Aniversário", "Dia das Mães", "Dia dos Pais", "Páscoa", "Dia das Crianças", "Ano Novo"],
        feats: ["Natal", "Aniversário", "Dia das Mães", "Dia dos Pais"],
      },
      {
        name: "Você e Eu",
        subs: ["Mamãe e Eu", "Papai e Eu", "Vovó e Vovô", "Irmãos e primos"],
        feats: ["Mamãe e Eu", "Papai e Eu", "Vovó e Vovô", "Irmãos e primos"],
      },
      {
        name: "Sentimentos",
        subs: ["Sentimentos", "Hora de Dormir", "Compartilhar", "Corpo"],
        feats: ["Sentimentos", "Hora de Dormir", "Compartilhar", "Corpo"],
      },
      {
        name: "Atividades",
        subs: ["Alfabetização", "Matemática", "Cores", "Higiene", "Vestir-se", "Animais", "Transporte"],
        feats: ["Alfabetização", "Matemática", "Cores", "Animais"],
      },
    ],
    cat_below: "Eternize momentos. Presenteie familiares com uma história inesquecível.",
    cat_below_lead: "Transforme uma foto em um livro personalizado, onde seu filho é o protagonista.",
    trust: "Encantando famílias do início ao fim",
    ba_before: "ANTES", ba_after: "DEPOIS", ba_caption: "Você envia a foto. A gente cria o encanto.",
    ba_preview: "PRÉ-VISUALIZAÇÃO",
    ba_title: "Antes e depois de verdade",
    ba_sub: "Fotos reais transformadas em personagens ilustrados.",
    ba_pairs: ["Do berço para a aventura", "Uma menina cheia de imaginação", "Sorriso que vira personagem", "Da foto ao herói da história", "Todo mundo pode ser protagonista"],
    hiw_title: "Como funciona", hiw_sub: "Você envia a foto e nós transformamos seu pequeno em um personagem ilustrado, criando uma aventura personalizada.",
    hiw: [
      { t: "Você envia a foto", p: "Uma foto da criança já basta para começar." },
      { t: "Criamos o personagem e a história", p: "Ilustração fiel à foto e um texto só de vocês." },
      { t: "Sua criança ganha o livro", p: "Páginas ilustradas para guardar para sempre." },
    ],
    shot_title: "Dicas para a foto perfeita",
    shot_sub: "Envie uma foto nítida da criança, com o rosto centralizado.",
    shots: ["Nítida, bem iluminada e centralizada", "Mais de uma pessoa na foto", "Rosto de lado"],
    hero_books: [
      "Martin, o Grande Goleiro do Chile",
      "Emilia e os Primeiros Passos da Bailarina",
      "Antonio e sua Bicicleta",
      "Maria Jesus e a Disciplina no Hockey",
      "Facundo e o Motocross com Cuidado",
    ],
    vid_title: "Vídeos narrados", vid_sub: "A mesma história ganha voz, trilha e movimento — perfeita para assistir em família.",
    vid_dur: "~2 min", vid_cta: "Criar meu vídeo",
    videos: [
      { t: "Lia e o Fundo do Mar", p: "Uma aventura no oceano com narração encantadora." },
      { t: "Sofia e a Floresta Encantada", p: "Bichinhos gentis e luzes de vaga-lume, com trilha suave." },
      { t: "Matteo e o Mundo dos Dinossauros", p: "Uma viagem ao vale dos dinossauros, com voz e trilha." },
    ],
    vid_soon: "Em breve",
    book_badge: "Exemplo real",
    story_title: "Folheie nossos livros",
    story_sub: "Livros criados pela plataforma a partir de uma única foto — escolha um exemplo.",
    story_hint: "Clique nas laterais do livro (ou use as setas) para virar as páginas.",
    chloe_title: "A História de Chloe",
    fmt_title: "Escolha o formato", fmt_sub: "Do mesmo personagem, três formas de guardar a história.",
    formats: [
      { t: "Livro em PDF", p: "Capa e páginas ilustradas, prontas na plataforma. O impresso é sob consulta.", feats: ["Capa + páginas ilustradas", "PDF na hora", "Personagem fiel à foto"], cta: "Criar meu livro", badge: "Mais amado" },
      { t: "Vídeo narrado", p: "A história ganha voz e trilha, perfeita para assistir em família.", feats: ["Narração encantadora", "Cenas ilustradas", "Fácil de compartilhar"], cta: "Criar meu vídeo", badge: "" },
      { t: "Animação", p: "O personagem ganha vida numa animação curta.", feats: ["Movimento e magia", "Baseada na sua história", "Um presente diferente"], cta: "Criar animação", badge: "" },
    ],
    cat_title: "Nossos livros", cat_sub: "Cada tema vira uma história ilustrada com seu filho como protagonista.",
    personalize: "Personalizar",
    a11y_theme: "Alternar tema claro/escuro",
    a11y_menu: "Menu",
    a11y_slide: "Slide",
    photo_real_alt: "Foto de exemplo da criança",
    fb_prev: "Página anterior",
    fb_next: "Próxima página",
    fb_turn: "Virar página",
    fb_cover: "Capa",
    privacy_link: "Privacidade",
    terms_link: "Termos",
    catalog: [
      { t: "Martin, o Grande Goleiro do Chile", p: "Goleiro que cai, levanta e defende: coragem e perseverança no campo.", cover: "Hard", size: "M", tag: "Esporte e coragem", quote: "Cair, levantar e continuar!" },
      { t: "Emilia e os Primeiros Passos da Bailarina", p: "Primeiros passos no ballet com disciplina, equilíbrio e confiança.", cover: "Soft", size: "M", tag: "Ballet e sonhos", quote: "Pequenos passos, grandes conquistas." },
      { t: "Antonio e sua Bicicleta", p: "Pedalar, aprender e explorar o mundo em pequenas aventuras.", cover: "Soft", size: "M", tag: "Aventura e movimento", quote: "Pedalar, aprender e sorrir!" },
      { t: "Aprendendo o Alfabeto com a Sofia", p: "Letras e descobertas na floresta, alfabetizar brincando.", cover: "Soft", size: "M", tag: "Alfabetizar brincando", quote: "Cada letra abre um mundo novo." },
      { t: "Bruno em uma aventura animal", p: "Conhecer animais e cuidar da natureza numa jornada gentil.", cover: "Soft", size: "M", tag: "Animais e natureza", quote: "Cada animal é especial — e juntos cuidamos do mundo." },
      { t: "Cristobal e seu Esporte Favorito", p: "No caiaque, equilíbrio, coragem e respeito pelo rio.", cover: "Hard", size: "M", tag: "Esporte e coragem", quote: "Pequenas remadas, grandes conquistas." },
    ],
    promise_title: "Cada detalhe pensado para ser especial",
    promise_sub: "Do envio da foto à prévia, tudo é feito para o livro ficar pronto para presentear.",
    promise: [
      { t: "Privacidade da foto", p: "A foto que você envia é usada só para criar o livro — nunca para divulgação. Os exemplos desta página são demonstrações da plataforma." },
      { t: "Impressão pensada como presente", p: "Preparado para ficar lindo em mãos, na leitura em família e na hora de entregar." },
      { t: "Prévia antes de avançar", p: "Você vê a capa e as páginas e entende o que está criando antes de finalizar." },
      { t: "Entrega sem complicação", p: "O PDF fica pronto na plataforma. O livro impresso é sob consulta — em até 24h enviamos a cotação e o prazo." },
    ],
    faq_title: "Perguntas frequentes", faq_sub: "Tudo o que você precisa saber.",
    faq: [
      { q: "Como crio um livro personalizado?", a: "Escolha um tema, envie uma foto da criança e adicione o nome e uma dedicatória. A IA transforma a foto em ilustrações e você vê a prévia antes de finalizar." },
      { q: "Posso ver o livro antes?", a: "Sim! Você recebe uma prévia completa (capa e páginas) antes de baixar ou pedir a impressão." },
      { q: "A foto e os dados da criança estão seguros?", a: "Sim. Usamos a foto que você envia apenas para criar o livro e não compartilhamos seus dados. Os exemplos da página inicial são demonstrações, separados do que você envia." },
      { q: "Recebo digital ou impresso?", a: "O e-book digital fica pronto na plataforma. Se quiser o impresso, peça a cotação depois de aprovar o livro." },
      { q: "Posso pedir alterações?", a: "Pode! Ajuste o nome, a dedicatória e regenere as ilustrações na prévia até ficar do seu jeito." },
      { q: "Como funciona o vídeo narrado?", a: "Depois do ebook pronto, na tela de resultado você pode gerar o vídeo narrado (voz + cenas ilustradas) ou uma animação curta do personagem." },
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
    band_cta: "Criar minha conta",
    tagline: "Feito com amor. Criado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  en: {
    nav: ["How it works", "Books", "Videos", "FAQ"],
    reviews_link: "Reviews",
    my_books: "My Books",
    our_story: "Personalization",
    see_all_books: "See all books",
    view_all: "View all",
    cats_label: "Categories",
    font_label: "Cover font",
    explore: "Explore now",
    eyebrow: "Preserve moments. Gift your family an unforgettable story.",
    h_pre: "Turn a photo into an ", w1: "unforgettable story", c1: ", where your child is the ", w2: "hero", h_suf: " !",
    lead: "You send the photo and we turn your little one into an illustrated character, creating an adventure made just for them — a book to gift the family and keep forever.",
    cta_play: "Create my account",
    hero_cta: "Create my book",
    cta_story: "Create my story",
    hero_sign: "One photo. One story. One lasting memory.",
    cats: [
      {
        name: "Favorite Adventures",
        subs: ["Adventure", "Fantasy", "Dinosaurs", "Under the sea", "Space", "Princesses", "Superheroes"],
        feats: ["Learning the Alphabet with Sofia", "Bruno on an Animal Adventure", "Cristobal and His Favorite Sport", "Learning the Alphabet with Sofia"],
      },
      {
        name: "Special Occasions",
        subs: ["Christmas", "Birthday", "Mother's Day", "Father's Day", "Easter", "Children's Day", "New Year"],
        feats: ["Christmas", "Birthday", "Mother's Day", "Father's Day"],
      },
      {
        name: "You and Me",
        subs: ["Mommy and Me", "Daddy and Me", "Grandma and Grandpa", "Siblings and cousins"],
        feats: ["Mommy and Me", "Daddy and Me", "Grandma and Grandpa", "Siblings and cousins"],
      },
      {
        name: "Feelings",
        subs: ["Feelings", "Bedtime", "Sharing", "Body"],
        feats: ["Feelings", "Bedtime", "Sharing", "Body"],
      },
      {
        name: "Activities",
        subs: ["Literacy", "Math", "Colors", "Hygiene", "Getting dressed", "Animals", "Transport"],
        feats: ["Literacy", "Math", "Colors", "Animals"],
      },
    ],
    cat_below: "Preserve moments. Gift your family an unforgettable story.",
    cat_below_lead: "Turn a photo into a personalized book, where your child is the hero.",
    trust: "Delighting families from start to finish",
    ba_before: "BEFORE", ba_after: "AFTER", ba_caption: "You send the photo. We create the magic.",
    ba_preview: "PREVIEW",
    ba_title: "Real before and after",
    ba_sub: "Real photos turned into illustrated characters.",
    ba_pairs: ["From crib to adventure", "A girl full of imagination", "A smile that becomes a character", "From photo to story hero", "Anyone can be the hero"],
    hiw_title: "How it works", hiw_sub: "You send the photo and we turn your little one into an illustrated character, creating a personalized adventure.",
    hiw: [
      { t: "You send the photo", p: "One photo of your child is all it takes to begin." },
      { t: "We create the character and story", p: "An illustration true to the photo and a story that's all yours." },
      { t: "Your child gets the book", p: "Illustrated pages to keep forever." },
    ],
    shot_title: "Tips for the perfect photo",
    shot_sub: "Upload a clear photo of your child with the face centered.",
    shots: ["Clear, well-lit and centered", "More than one person in the photo", "Face at an angle"],
    hero_books: [
      "Martin, the Great Goalkeeper of Chile",
      "Emilia and the Ballerina's First Steps",
      "Antonio and His Bicycle",
      "Maria Jesus and Hockey Discipline",
      "Facundo and Careful Motocross",
    ],
    vid_title: "Narrated videos", vid_sub: "The same story gains voice, music and motion — perfect to watch together.",
    vid_dur: "~2 min", vid_cta: "Create my video",
    videos: [
      { t: "Lia and the Deep Sea", p: "An ocean adventure with enchanting narration." },
      { t: "Sofia and the Enchanted Forest", p: "Gentle little creatures and firefly lights, with a soft soundtrack." },
      { t: "Matteo and the Dinosaur World", p: "A journey through the dinosaur valley, with voice and music." },
    ],
    vid_soon: "Coming soon",
    book_badge: "Real example",
    story_title: "Flip through our books",
    story_sub: "Books created by the platform from a single photo — pick an example.",
    story_hint: "Click the sides of the book (or use the arrows) to turn the pages.",
    chloe_title: "Chloe's Story",
    fmt_title: "Choose the format", fmt_sub: "From the same character, three ways to keep the story.",
    formats: [
      { t: "PDF book", p: "Cover and illustrated pages, ready on the platform. Print is quoted on request.", feats: ["Cover + illustrated pages", "PDF right away", "Character true to the photo"], cta: "Create my book", badge: "Most loved" },
      { t: "Narrated video", p: "The story gets a voice and music, perfect to watch together.", feats: ["Enchanting narration", "Illustrated scenes", "Easy to share"], cta: "Create my video", badge: "" },
      { t: "Animation", p: "The character comes alive in a short animation.", feats: ["Movement and magic", "Based on your story", "A different gift"], cta: "Create animation", badge: "" },
    ],
    cat_title: "Our books", cat_sub: "Each theme becomes an illustrated story with your child as the hero.",
    personalize: "Personalize",
    a11y_theme: "Toggle light/dark theme",
    a11y_menu: "Menu",
    a11y_slide: "Slide",
    photo_real_alt: "Example photo of the child",
    fb_prev: "Previous page",
    fb_next: "Next page",
    fb_turn: "Turn page",
    fb_cover: "Cover",
    privacy_link: "Privacy",
    terms_link: "Terms",
    catalog: [
      { t: "Martin, the Great Goalkeeper of Chile", p: "A goalkeeper who falls, rises and defends: courage and grit on the field.", cover: "Hard", size: "M", tag: "Sport and courage", quote: "Fall, rise, and keep going!" },
      { t: "Emilia and the Ballerina's First Steps", p: "Ballet's first steps with discipline, balance and confidence.", cover: "Soft", size: "M", tag: "Ballet and dreams", quote: "Small steps, big achievements." },
      { t: "Antonio and His Bicycle", p: "Pedal, learn and explore the world in small adventures.", cover: "Soft", size: "M", tag: "Adventure and movement", quote: "Pedal, learn and smile!" },
      { t: "Learning the Alphabet with Sofia", p: "Letters and forest discoveries — literacy through play.", cover: "Soft", size: "M", tag: "Literacy through play", quote: "Every letter opens a new world." },
      { t: "Bruno on an Animal Adventure", p: "Meet animals and care for nature on a gentle journey.", cover: "Soft", size: "M", tag: "Animals and nature", quote: "Every animal is special — and together we care for the world." },
      { t: "Cristobal and His Favorite Sport", p: "On the kayak: balance, courage and respect for the river.", cover: "Hard", size: "M", tag: "Sport and courage", quote: "Small paddles, big victories." },
    ],
    promise_title: "Every detail crafted to feel special",
    promise_sub: "From the photo to the preview, everything is made so the book is ready to gift.",
    promise: [
      { t: "Photo privacy", p: "The photo you upload is used only to create the book — never for promotion. The examples on this page are platform demos." },
      { t: "Print made as a gift", p: "Prepared to look beautiful in hand, in shared reading and at the moment you give it." },
      { t: "Preview before you continue", p: "You see the cover and pages and understand what you're creating before finishing." },
      { t: "Hassle-free delivery", p: "The PDF is ready on the platform. Printed books are quoted on request — we send price and timing within 24 hours." },
    ],
    faq_title: "Frequently asked questions", faq_sub: "Everything you need to know.",
    faq: [
      { q: "How do I create a personalized book?", a: "Pick a theme, upload a photo of your child and add the name and a dedication. The AI turns the photo into illustrations and you see a preview before finishing." },
      { q: "Can I see the book before?", a: "Yes! You get a full preview (cover and pages) before downloading or ordering the print." },
      { q: "Are my child's photo and data safe?", a: "Yes. We use the photo you upload only to create the book and never share your data. Homepage examples are demos, separate from what you send." },
      { q: "Digital or printed?", a: "The digital e-book is ready on the platform. If you want a printed copy, request a quote after you approve the book." },
      { q: "Can I request changes?", a: "You can! Adjust the name, the dedication and regenerate the illustrations in the preview." },
      { q: "How does the narrated video work?", a: "After the ebook is ready, on the result screen you can generate a narrated video (voice + illustrated scenes) or a short character animation." },
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
    band_cta: "Create my account",
    tagline: "Made with love. Created to enchant.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  es: {
    nav: ["Cómo funciona", "Libros", "Videos", "FAQ"],
    reviews_link: "Reseñas",
    my_books: "Mis Libros",
    our_story: "Personalización",
    see_all_books: "Ver todos los libros",
    view_all: "Ver todos",
    cats_label: "Categorías",
    font_label: "Fuente del título",
    explore: "Explorar ahora",
    eyebrow: "Eterniza momentos. Regala a tu familia una historia inolvidable.",
    h_pre: "Convierte una foto en una ", w1: "historia inolvidable", c1: ", donde tu hijo es el ", w2: "protagonista", h_suf: " !",
    lead: "Envías la foto y transformamos a tu pequeño en un personaje ilustrado, creando una aventura personalizada especialmente para él — un libro para regalar a la familia y guardar para siempre.",
    cta_play: "Crear mi cuenta",
    hero_cta: "Crear mi libro",
    cta_story: "Crear mi historia",
    hero_sign: "Una foto. Una historia. Una memoria eterna.",
    cats: [
      {
        name: "Aventuras Favoritas",
        subs: ["Aventura", "Fantasía", "Dinosaurios", "Fondo del mar", "Espacio", "Princesas", "Superhéroes"],
        feats: ["Aprendiendo el alfabeto con Sofia", "Bruno en una aventura animal", "Cristobal y su deporte favorito", "Aprendiendo el alfabeto con Sofia"],
      },
      {
        name: "Ocasiones Especiales",
        subs: ["Navidad", "Cumpleaños", "Día de la Madre", "Día del Padre", "Pascua", "Día del Niño", "Año Nuevo"],
        feats: ["Navidad", "Cumpleaños", "Día de la Madre", "Día del Padre"],
      },
      {
        name: "Tú y Yo",
        subs: ["Mamá y Yo", "Papá y Yo", "Abuela y Abuelo", "Hermanos y primos"],
        feats: ["Mamá y Yo", "Papá y Yo", "Abuela y Abuelo", "Hermanos y primos"],
      },
      {
        name: "Sentimientos",
        subs: ["Sentimientos", "Hora de Dormir", "Compartir", "Cuerpo"],
        feats: ["Sentimientos", "Hora de Dormir", "Compartir", "Cuerpo"],
      },
      {
        name: "Actividades",
        subs: ["Alfabetización", "Matemáticas", "Colores", "Higiene", "Vestirse", "Animales", "Transporte"],
        feats: ["Alfabetización", "Matemáticas", "Colores", "Animales"],
      },
    ],
    cat_below: "Eterniza momentos. Regala a tu familia una historia inolvidable.",
    cat_below_lead: "Convierte una foto en un libro personalizado, donde tu hijo es el protagonista.",
    trust: "Encantando a las familias de principio a fin",
    ba_before: "ANTES", ba_after: "DESPUÉS", ba_caption: "Tú envías la foto. Nosotros creamos la magia.",
    ba_preview: "VISTA PREVIA",
    ba_title: "Antes y después de verdad",
    ba_sub: "Fotos reales convertidas en personajes ilustrados.",
    ba_pairs: ["De la cuna a la aventura", "Una niña llena de imaginación", "Una sonrisa que se vuelve personaje", "De la foto al héroe de la historia", "Cualquiera puede ser protagonista"],
    hiw_title: "Cómo funciona", hiw_sub: "Envías la foto y transformamos a tu pequeño en un personaje ilustrado, creando una aventura personalizada.",
    hiw: [
      { t: "Tú envías la foto", p: "Una foto del niño ya basta para empezar." },
      { t: "Creamos el personaje y la historia", p: "Ilustración fiel a la foto y un texto solo de ustedes." },
      { t: "Tu niño recibe el libro", p: "Páginas ilustradas para guardar para siempre." },
    ],
    shot_title: "Consejos para la foto perfecta",
    shot_sub: "Envía una foto nítida del niño, con el rostro centrado.",
    shots: ["Nítida, bien iluminada y centrada", "Más de una persona en la foto", "Rostro de lado"],
    hero_books: [
      "Martin, el gran arquero de Chile",
      "Emilia y los primeros pasos de la bailarina",
      "Antonio y su bicicleta",
      "Maria Jesus y la disciplina en el hockey",
      "Facundo y el motocross con cuidado",
    ],
    vid_title: "Videos narrados", vid_sub: "La misma historia gana voz, música y movimiento — perfecta para ver en familia.",
    vid_dur: "~2 min", vid_cta: "Crear mi video",
    videos: [
      { t: "Lia y el Fondo del Mar", p: "Una aventura en el océano con narración encantadora." },
      { t: "Sofia y el Bosque Encantado", p: "Animalitos gentiles y luces de luciérnaga, con una banda suave." },
      { t: "Matteo y el Mundo de los Dinosaurios", p: "Un viaje al valle de los dinosaurios, con voz y música." },
    ],
    vid_soon: "Pronto",
    book_badge: "Ejemplo real",
    story_title: "Hojea nuestros libros",
    story_sub: "Libros creados por la plataforma a partir de una sola foto — elige un ejemplo.",
    story_hint: "Haz clic en los laterales del libro (o usa las flechas) para pasar las páginas.",
    chloe_title: "La Historia de Chloe",
    fmt_title: "Elige el formato", fmt_sub: "Del mismo personaje, tres formas de guardar la historia.",
    formats: [
      { t: "Libro en PDF", p: "Portada y páginas ilustradas, listas en la plataforma. El impreso es bajo consulta.", feats: ["Portada + páginas ilustradas", "PDF al instante", "Personaje fiel a la foto"], cta: "Crear mi libro", badge: "Más querido" },
      { t: "Video narrado", p: "La historia gana voz y música, perfecta para ver en familia.", feats: ["Narración encantadora", "Escenas ilustradas", "Fácil de compartir"], cta: "Crear mi video", badge: "" },
      { t: "Animación", p: "El personaje cobra vida en una animación corta.", feats: ["Movimiento y magia", "Basada en tu historia", "Un regalo diferente"], cta: "Crear animación", badge: "" },
    ],
    cat_title: "Nuestros libros", cat_sub: "Cada tema se vuelve una historia ilustrada con tu hijo como protagonista.",
    personalize: "Personalizar",
    a11y_theme: "Cambiar tema claro/oscuro",
    a11y_menu: "Menú",
    a11y_slide: "Diapositiva",
    photo_real_alt: "Foto de ejemplo del niño",
    fb_prev: "Página anterior",
    fb_next: "Página siguiente",
    fb_turn: "Pasar página",
    fb_cover: "Portada",
    privacy_link: "Privacidad",
    terms_link: "Términos",
    catalog: [
      { t: "Martin, el gran arquero de Chile", p: "Arquero que cae, se levanta y defiende: coraje y perseverancia en el campo.", cover: "Hard", size: "M", tag: "Deporte y coraje", quote: "¡Caer, levantarse y seguir!" },
      { t: "Emilia y los primeros pasos de la bailarina", p: "Primeros pasos en el ballet con disciplina, equilibrio y confianza.", cover: "Soft", size: "M", tag: "Ballet y sueños", quote: "Pequeños pasos, grandes logros." },
      { t: "Antonio y su bicicleta", p: "Pedalear, aprender y explorar el mundo en pequeñas aventuras.", cover: "Soft", size: "M", tag: "Aventura y movimiento", quote: "¡Pedalear, aprender y sonreír!" },
      { t: "Aprendiendo el alfabeto con Sofia", p: "Letras y descubrimientos en el bosque, alfabetizar jugando.", cover: "Soft", size: "M", tag: "Alfabetizar jugando", quote: "Cada letra abre un mundo nuevo." },
      { t: "Bruno en una aventura animal", p: "Conocer animales y cuidar la naturaleza en una jornada gentil.", cover: "Soft", size: "M", tag: "Animales y naturaleza", quote: "Cada animal es especial — y juntos cuidamos el mundo." },
      { t: "Cristobal y su deporte favorito", p: "En el kayak: equilibrio, coraje y respeto por el río.", cover: "Hard", size: "M", tag: "Deporte y coraje", quote: "Pequeñas paladas, grandes conquistas." },
    ],
    promise_title: "Cada detalle pensado para ser especial",
    promise_sub: "Del envío de la foto a la vista previa, todo está hecho para que el libro quede listo para regalar.",
    promise: [
      { t: "Privacidad de la foto", p: "La foto que envías se usa solo para crear el libro — nunca para promoción. Los ejemplos de esta página son demostraciones de la plataforma." },
      { t: "Impresión pensada como regalo", p: "Preparado para verse hermoso en las manos, en la lectura en familia y al momento de entregarlo." },
      { t: "Vista previa antes de avanzar", p: "Ves la portada y las páginas y entiendes lo que estás creando antes de finalizar." },
      { t: "Entrega sin complicaciones", p: "El PDF queda listo en la plataforma. El libro impreso es bajo consulta — en hasta 24h enviamos la cotización y el plazo." },
    ],
    faq_title: "Preguntas frecuentes", faq_sub: "Todo lo que necesitas saber.",
    faq: [
      { q: "¿Cómo creo un libro personalizado?", a: "Elige un tema, envía una foto del niño y agrega el nombre y una dedicatoria. La IA transforma la foto en ilustraciones y ves la vista previa antes de finalizar." },
      { q: "¿Puedo ver el libro antes?", a: "¡Sí! Recibes una vista previa completa (portada y páginas) antes de descargar o pedir la impresión." },
      { q: "¿La foto y los datos del niño están seguros?", a: "Sí. Usamos la foto que envías solo para crear el libro y no compartimos tus datos. Los ejemplos de la página inicial son demostraciones, separados de lo que tú envías." },
      { q: "¿Recibo digital o impreso?", a: "El e-book digital queda listo en la plataforma. Si quieres el impreso, pide la cotización después de aprobar el libro." },
      { q: "¿Puedo pedir cambios?", a: "¡Puedes! Ajusta el nombre, la dedicatoria y regenera las ilustraciones en la vista previa hasta que quede a tu gusto." },
      { q: "¿Cómo funciona el video narrado?", a: "Después del ebook listo, en la pantalla de resultado puedes generar el video narrado (voz + escenas ilustradas) o una animación corta del personaje." },
    ],
    rev_title: "Lo que dicen las familias", rev_sub: "Historias que se volvieron recuerdos para siempre.",
    reviews: [
      { q: "Mi hijo pide leer su libro todas las noches. ¡Emocionante verlo como héroe!", name: "Ana C." },
      { q: "Envié una foto y recibí un libro hermoso. Se volvió el regalo de cumpleaños de la abuela.", name: "Rafael M." },
      { q: "La ilustración quedó idéntica a mi bebé. Lo vamos a guardar para siempre.", name: "Juliana P." },
      { q: "El video narrado emocionó a toda la familia. Vale cada segundo.", name: "Marcos y Bia" },
    ],
    features: ["Historias personalizadas", "Conexión en familia", "Recuerdos que quedan para siempre", "Un regalo inolvidable"],
    band_title: "¿Listo para ser el protagonista?",
    band_sub: "Envía tu foto y recibe una historia única, creada solo para ti.",
    band_cta: "Crear mi cuenta",
    tagline: "Hecho con amor. Creado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
} as const;

export function Landing() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [openCat, setOpenCat] = useState<number | null>(null);
  const [mobileCat, setMobileCat] = useState<number | null>(null);
  const [lang, setLang] = useState<Lang>(() => {
    try {
      const s = localStorage.getItem("lang");
      if (s === "pt" || s === "en" || s === "es") return s;
    } catch { /* ignore */ }
    return "pt";
  });
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try { const s = localStorage.getItem("theme"); if (s === "light" || s === "dark") return s; } catch { /* ignore */ }
    return "dark";
  });
  const [exBook, setExBook] = useState(0);
  const [coverFont] = useState<CoverFont>(() => {
    try {
      const s = localStorage.getItem("coverFont");
      if (s === "fredoka" || s === "baloo" || s === "lilita") return s;
    } catch { /* ignore */ }
    return "fredoka";
  });
  const t = I18N[lang];
  const navHrefs = ["#como", "#catalogo", "#videos", "#faq"];
  const exampleBooks = HERO_BOOKS.map((b, i) => ({
    title: t.hero_books[i],
    tab: b.tab,
    cover: b.cover,
    pages: [b.cover, b.page],
  }));
  const flipLabels = { prev: t.fb_prev, next: t.fb_next, turn: t.fb_turn, cover: t.fb_cover };
  const navCats = t.cats.map((cat, i) => ({
    ...cat,
    color: NAV_CAT_META[i].color,
    subs: cat.subs.map((label, j) => ({ label, href: NAV_CAT_META[i].subs[j].href })),
    feats: cat.feats.map((label, j) => ({
      label,
      href: NAV_CAT_META[i].feats[j].href,
      img: NAV_CAT_META[i].feats[j].img,
    })),
  }));

  const featIcons = [IcSparkle, IcHeart, IcBook, IcGift];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = lang === "en" ? "en" : lang === "es" ? "es" : "pt-BR";
    try { localStorage.setItem("lang", lang); } catch { /* ignore */ }
  }, [lang]);

  useEffect(() => {
    const els = rootRef.current?.querySelectorAll(".reveal") ?? [];
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    els.forEach((el, i) => { (el as HTMLElement).style.transitionDelay = `${(i % 3) * 0.1}s`; io.observe(el); });
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    try { localStorage.setItem("coverFont", coverFont); } catch { /* ignore */ }
  }, [coverFont]);

  useEffect(() => {
    if (!navOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setNavOpen(false);
        setMobileCat(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navOpen]);

  const closeNav = () => {
    setNavOpen(false);
    setMobileCat(null);
    setOpenCat(null);
  };

  return (
    <div className={`kid cover-${coverFont}`} ref={rootRef} id="top">
      <div className="sky" aria-hidden>
        <IcStar className="dstar d1" /><IcStar className="dstar d2" /><IcSparkle className="dstar d3" /><IcStar className="dstar d4" />
        <svg className="dmoon m1" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#f4b740" /></svg>
        <svg className="dmoon m2" viewBox="0 0 24 24" aria-hidden><path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#7fb2e3" /></svg>
      </div>

      <header className="khead">
        <div className="khead-inner">
        <a href="#top" className="kbrand"><img src={logo} alt="Story.R.Us" /></a>
        <div className="khead-main">
          <div className="khead-top">
            <div className="khead-top-inner">
              <div className="khead-utils">
                <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t.a11y_theme}>
                  {theme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
                </button>
                <div className="lang" role="group" aria-label="Idioma / Language / Idioma">
                  <button className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")}>PT</button>
                  <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
                  <button className={lang === "es" ? "on" : ""} onClick={() => setLang("es")}>ES</button>
                </div>
                <button
                  className="khamb"
                  aria-label={t.a11y_menu}
                  aria-expanded={navOpen}
                  aria-controls="site-menu"
                  onClick={() => setNavOpen((v) => !v)}
                >☰</button>
              </div>
            </div>
          </div>
          <div className="khead-bar">
            <div className="khead-bar-inner">
              <nav className="kcats" aria-label={t.cats_label}>
                {navCats.map((cat, i) => (
                  <div
                    key={cat.name}
                    className={`kcat${openCat === i ? " open" : ""}`}
                    onMouseEnter={() => setOpenCat(i)}
                    onMouseLeave={() => setOpenCat(null)}
                  >
                    <button
                      type="button"
                      className="kcat-btn"
                      aria-expanded={openCat === i}
                      aria-haspopup="true"
                      onClick={() => setOpenCat(openCat === i ? null : i)}
                    >
                      <span className="kcat-dot" style={{ background: cat.color, boxShadow: `0 0 10px ${cat.color}` }} />
                      {cat.name}
                    </button>
                    <div className="kcat-panel">
                      <ul className="kcat-subs">
                        {cat.subs.map((sub) => (
                          <li key={sub.label}><Link to={sub.href} onClick={closeNav}>{sub.label}</Link></li>
                        ))}
                      </ul>
                      <div className="kcat-feats">
                        {cat.feats.map((feat) => (
                          <Link key={`${feat.href}-${feat.label}`} className="kcat-feat" to={feat.href} onClick={closeNav}>
                            <span className="kcat-feat-cover">
                              <img src={exUrl(feat.img)} alt="" />
                            </span>
                            <span>{feat.label}</span>
                          </Link>
                        ))}
                        <Link to="/app" className="kbtn kbtn-go kcat-all" onClick={closeNav}>{t.view_all}</Link>
                      </div>
                    </div>
                  </div>
                ))}
                <a href="#promessa" className="kcat-btn" onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#5ec4a8", boxShadow: "0 0 10px rgba(94,196,168,.9)" }} />
                  {t.our_story}
                </a>
                <a href="#reviews" className="kcat-btn" onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#f4b740", boxShadow: "0 0 10px rgba(244,183,64,.95)" }} />
                  {t.reviews_link}
                </a>
              </nav>
              <div className="khead-links">
                <Link to="/app" className="kbtn kbtn-primary">{t.cta_play}</Link>
              </div>
            </div>
          </div>
        </div>
        <nav id="site-menu" className={`kmobile${navOpen ? " open" : ""}`}>
          {navCats.map((cat, i) => (
            <div key={cat.name} className={`kmobile-cat${mobileCat === i ? " open" : ""}`}>
              <button
                type="button"
                className="kmobile-cat-btn"
                aria-expanded={mobileCat === i}
                onClick={() => setMobileCat(mobileCat === i ? null : i)}
              >
                <span className="kcat-dot" style={{ background: cat.color }} />
                {cat.name}
                <IcChevron className="faq-chev" />
              </button>
              <div className="kmobile-subs">
                <div className="kmobile-subs-inner">
                  {cat.subs.map((sub) => (
                    <Link key={sub.label} to={sub.href} onClick={closeNav}>{sub.label}</Link>
                  ))}
                </div>
              </div>
            </div>
          ))}
          <a href="#promessa" onClick={closeNav}>{t.our_story}</a>
          <a href="#reviews" onClick={closeNav}>{t.reviews_link}</a>
          {t.nav.map((label, i) => (
            <a key={label} href={navHrefs[i]} onClick={closeNav}>{label}</a>
          ))}
          <Link to="/app" className="kbtn kbtn-primary" onClick={closeNav}>{t.cta_play}</Link>
        </nav>
        </div>
      </header>

      {/* HERO — proposta de valor + flipbook */}
      <section className="kbanner-hero" aria-label={t.hero_sign}>
        <div className="khero-intro">
          <span className="keyebrow"><IcSparkle className="ei" /> {t.hero_sign}</span>
          <h1>{t.h_pre}<em className="g1">{t.w1}</em>{t.c1}<em className="g2">{t.w2}</em>{t.h_suf}</h1>
        </div>
        <div className="khero-flip">
          <div className="ex-tabs khero-tabs" role="tablist" aria-label={t.story_title}>
            {exampleBooks.map((b, i) => (
              <button
                key={b.title}
                type="button"
                className={`ex-tab${i === exBook ? " on" : ""}`}
                onClick={() => setExBook(i)}
                role="tab"
                id={`ex-tab-${i}`}
                aria-selected={i === exBook}
                aria-controls="ex-book-panel"
              >
                <img className="ex-tab-cover" src={exUrl(b.tab)} alt="" />
                <span>{b.title}</span>
              </button>
            ))}
          </div>
          <div id="ex-book-panel" role="tabpanel" aria-labelledby={`ex-tab-${exBook}`}>
            <FlipBook
              key={exBook}
              pages={exampleBooks[exBook].pages}
              labels={flipLabels}
            />
          </div>
        </div>
        <div className="khero-after">
          <span className="keyebrow"><IcSparkle className="ei" /> {t.eyebrow}</span>
          <Link to="/app" className="kbtn kbtn-primary">{t.hero_cta}</Link>
        </div>
      </section>

      {/* COMO FUNCIONA + DICAS */}
      <section className="ksection ksection-como" id="como">
        <div className="como-panel reveal">
          <h2 className="ktitle">{t.hiw_title}</h2>
          <p className="ksub">{t.hiw_sub}</p>
          <div className="shot-tips">
            <h3>{t.shot_title}</h3>
            <p className="shot-sub">{t.shot_sub}</p>
            <div className="shot-grid">
              {SHOTS.map((s, i) => (
                <div className={`shot${s.ok ? " ok" : ""}`} key={i}>
                  <div className="shot-ava-wrap">
                    <div className="shot-ava">
                      {s.img ? (
                        <img src={exUrl(s.img)} alt={t.shots[i] || t.shot_title} loading="lazy" style={{ objectPosition: s.focus ?? "center center" }} />
                      ) : (
                        <ShotArt kind={s.art ?? "good"} />
                      )}
                    </div>
                    <span className="shot-badge">{s.ok ? <IcCheck /> : <IcClose />}</span>
                  </div>
                  {t.shots[i] ? <p>{t.shots[i]}</p> : null}
                </div>
              ))}
            </div>
          </div>
          <div className="howex">
            {t.hiw.map((h, i) => (
              <Fragment key={h.t}>
                <figure className={`howex-card${i === 0 ? " howex-card-face" : ""}${i === 1 ? " howex-card-avatar" : ""}${i === 2 ? " howex-card-page" : ""}`}>
                  <img src={exUrl(HOW_IMGS[i])} alt={h.t} loading="lazy" />
                  <span className="howex-num">{i + 1}</span>
                  <figcaption>
                    <h3>{h.t}</h3>
                    <p>{h.p}</p>
                  </figcaption>
                </figure>
                {i < t.hiw.length - 1 && <span className="howex-arrow" aria-hidden><IcArrow /></span>}
              </Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* NOSSOS LIVROS */}
      <section className="ksection" id="catalogo">
        <h2 className="ktitle reveal">{t.cat_title}</h2>
        <p className="ksub reveal">{t.cat_sub}</p>
        <div className="cat-grid">
          {t.catalog.map((c, i) => (
            <div className="cat-card reveal" key={c.t}>
              <div className="cat-display" style={{ background: BOOK3D[i].bg }}>
                <div className="cat-book">
                  <img src={exUrl(CATALOG_IMGS[i])} alt={c.t} />
                </div>
              </div>
              <div className="cat-body">
                <div className="cat-badges">
                  <span className="cat-cover-type">{c.cover}</span>
                  <span className="cat-size">{c.size}</span>
                  <span className="cat-tag">{c.tag}</span>
                </div>
                <h3>{c.t}</h3>
                <p>{c.p}</p>
                <Link to={`/app?tema=${CATALOG_THEMES[i]}`} className="kbtn kbtn-primary">{t.personalize}</Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* VÍDEOS NARRADOS */}
      <section className="ksection" id="videos">
        <h2 className="ktitle reveal">{t.vid_title}</h2>
        <p className="ksub reveal">{t.vid_sub}</p>
        <div className="vid-grid">
          {t.videos.map((v, i) => {
            const src = VIDEO_SRCS[i];
            const canPlay = Boolean(src);
            return (
              <figure className="vid-card reveal" key={v.t}>
                <div className="vid-thumb">
                  {canPlay && src ? (
                    <AutoMutedVideo key={src} src={exUrl(src)} poster={exUrl(VIDEO_IMGS[i])} />
                  ) : (
                    <button
                      type="button"
                      className="vid-play-btn"
                      aria-label={`${v.t} — ${t.vid_soon}`}
                      disabled
                    >
                      <img src={exUrl(VIDEO_IMGS[i])} alt={v.t} loading="lazy" />
                      <span className="vid-dur">{t.vid_soon}</span>
                    </button>
                  )}
                </div>
                <figcaption><h3>{v.t}</h3><p>{v.p}</p></figcaption>
              </figure>
            );
          })}
        </div>
        <div className="vid-cta"><Link to="/app" className="kbtn kbtn-primary big">{t.vid_cta}</Link></div>
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
          {t.nav.map((label, i) => { const Icon = FOOT_ICONS[i]; return (<a key={label} href={navHrefs[i]}><Icon className="ni" />{label}</a>); })}
        </div>
        <div className="kfoot-contacts">
          <a href={`mailto:${CONTACT_EMAIL}`} className="kfoot-contact">
            <IcMail className="ni" />
            <span>{CONTACT_EMAIL}</span>
          </a>
          <a
            href={`https://instagram.com/${CONTACT_INSTA}`}
            className="kfoot-contact"
            target="_blank"
            rel="noopener noreferrer"
          >
            <IcInstagram className="ni" />
            <span>@{CONTACT_INSTA}</span>
          </a>
          <Link to="/privacidade" className="kfoot-contact">{t.privacy_link}</Link>
          <Link to="/termos" className="kfoot-contact">{t.terms_link}</Link>
        </div>
        <p className="kfoot-tag"><IcHeart className="ci" /> {t.tagline}</p>
        <p className="kfoot-copy">{t.foot_copy}</p>
      </footer>
    </div>
  );
}
