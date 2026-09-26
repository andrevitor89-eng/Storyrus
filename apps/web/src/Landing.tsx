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
const CONTACT_EMAIL = "info@storyrus.ai";
const CONTACT_INSTA = "storyr.us";
const PROMISE_ICONS = [IcShield, IcGift, IcEye, IcTruck];
type CoverFont = "fredoka" | "baloo" | "lilita";
type HeroAsset = Record<Lang, string>;
const heroAsset = (pt: string, en = pt, es = en): HeroAsset => ({ pt, en, es });
/** Hero strip: capa, página aberta, criança lendo. Natal fica na abertura. */
const HERO_STRIP: { name: string; cover: HeroAsset; page: HeroAsset; photo: HeroAsset }[] = [
  {
    name: "Meme e Tata",
    cover: heroAsset("capa-natalmemetata.jpg", "capa-natalmemetata-en.jpg", "capa-natalmemetata-es.jpg"),
    page: heroAsset("pagina-natalmemetata.jpg", "pagina-natalmemetata-en.jpg", "pagina-natalmemetata-es.jpg"),
    photo: heroAsset("foto-natalmemetata.jpg", "foto-natalmemetata-en.jpg", "foto-natalmemetata-es.jpg"),
  },
  {
    name: "Nano",
    cover: heroAsset("capa-nanoaventuras.jpg", "capa-nanoaventuras-en.jpg", "capa-nanoaventuras-es.jpg"),
    page: heroAsset("pagina-nanoaventuras-en.jpg", "pagina-nanoaventuras-en.jpg", "pagina-nanoaventuras-es.jpg"),
    photo: heroAsset("foto-nanoaventuras-en.jpg", "foto-nanoaventuras-en.jpg", "foto-nanoaventuras-es.jpg"),
  },
  {
    name: "Amor de Bisavó",
    cover: heroAsset("capa-amordebisavo.jpg", "capa-amordebisavo-en.jpg", "capa-amordebisavo-es.jpg"),
    page: heroAsset("pagina-amordebisavo-en.jpg", "pagina-amordebisavo-en.jpg", "pagina-amordebisavo-es.jpg"),
    photo: heroAsset("foto-amordebisavo-en.jpg", "foto-amordebisavo-en.jpg", "foto-amordebisavo-es.jpg"),
  },
  {
    name: "Amor de Mãe",
    cover: heroAsset("capa-amordemae.jpg"),
    page: heroAsset("pagina-amordemae.jpg"),
    photo: heroAsset("foto-amordemae.jpg"),
  },
  {
    name: "Mako",
    cover: heroAsset("capa-mako-amigofiel.jpg", "capa-mako-amigofiel-en.jpg", "capa-mako-amigofiel-es.jpg"),
    page: heroAsset("pagina-mako-amigofiel.jpg", "pagina-mako-amigofiel-en.jpg", "pagina-mako-amigofiel-es.jpg"),
    photo: heroAsset("foto-mako-amigofiel.jpg", "foto-mako-amigofiel-en.jpg", "foto-mako-amigofiel-es.jpg"),
  },
  {
    name: "Martin",
    cover: heroAsset("capa-martin-goleiro.jpg"),
    page: heroAsset("pagina-martin-goleiro.jpg"),
    photo: heroAsset("foto-martin-goleiro.jpg"),
  },
  {
    name: "Emilia",
    cover: heroAsset("capa-emilia-bailarina.jpg"),
    page: heroAsset("pagina-emilia-bailarina.jpg"),
    photo: heroAsset("foto-emilia-bailarina.jpg"),
  },
  {
    name: "Antonio",
    cover: heroAsset("capa-antonio-bicicleta.jpg"),
    page: heroAsset("pagina-antonio-bicicleta.jpg"),
    photo: heroAsset("foto-antonio-bicicleta.jpg"),
  },
  {
    name: "Maria Jesus",
    cover: heroAsset("capa-mariajesus-hockey.jpg"),
    page: heroAsset("pagina-mariajesus-hockey.jpg"),
    photo: heroAsset("foto-mariajesus-hockey.jpg"),
  },
  {
    name: "Facundo",
    cover: heroAsset("capa-facundo-motocross.jpg"),
    page: heroAsset("pagina-facundo-motocross.jpg"),
    photo: heroAsset("foto-facundo-motocross.jpg"),
  },
];
/** Hero do /cartoon: só livros com visual de desenho. */
const HERO_STRIP_CARTOON: { name: string; cover: HeroAsset; page: HeroAsset; photo: HeroAsset }[] = [
  {
    name: "Floresta Encantada",
    cover: heroAsset("capa-floresta.jpg"),
    page: heroAsset("flor-2.jpg"),
    photo: heroAsset("flor-6.jpg"),
  },
  {
    name: "Dino",
    cover: heroAsset("capa-dino2.jpg"),
    page: heroAsset("dino-2.jpg"),
    photo: heroAsset("dino-6.jpg"),
  },
  {
    name: "Circo",
    cover: heroAsset("capa-circo.jpg"),
    page: heroAsset("circo-2.jpg"),
    photo: heroAsset("circo-6.jpg"),
  },
  {
    name: "Oceano",
    cover: heroAsset("capa-oceano.jpg"),
    page: heroAsset("mar-2.jpg"),
    photo: heroAsset("mar-6.jpg"),
  },
  {
    name: "Amazônia",
    cover: heroAsset("capa-amazonia.jpg"),
    page: heroAsset("amazonia-3.jpg"),
    photo: heroAsset("amazonia-6.jpg"),
  },
];

/* ------- exemplos reais em apps/web/public/exemplos/ ------- */
const HOW_IMGS = ["dica-boa.png", "personagem-avatar.jpg", "cena-dino-floresta.jpg"];
const SHOTS: { img?: string; art?: "good" | "multi" | "side" | "covered"; ok: boolean; focus?: string }[] = [
  { img: "dica-boa.png", ok: true, focus: "center center" },
  { img: "dica-multi.png", ok: false, focus: "68% 38%" },
  { img: "dica-lado.png", ok: false, focus: "78% 32%" },
];
/** Reviews strip: one lifestyle photo per book (PT/default), never EN/ES duplicates of the same scene. */
const REVIEW_PHOTOS = [
  { tab: "foto-martin-goleiro.jpg", name: "Martin" },
  { tab: "foto-nicolas-maefilho.jpg", name: "Nicolas" },
  { tab: "foto-emilia-bailarina.jpg", name: "Emilia" },
  { tab: "foto-amordemae.jpg", name: "Amor de Mãe" },
  { tab: "foto-antonio-bicicleta.jpg", name: "Antonio" },
  { tab: "foto-mamaepapaimatteo-en.jpg", name: "Matteo" },
  { tab: "foto-mariajesus-hockey.jpg", name: "Maria Jesus" },
  { tab: "foto-amordebisavo.jpg", name: "Amor de Bisavó" },
  { tab: "foto-facundo-motocross.jpg", name: "Facundo" },
  { tab: "foto-natalmemetata.jpg", name: "Meme e Tata" },
  { tab: "foto-ester.png", name: "Ester" },
  { tab: "foto-raquel-papai.png", name: "Raquel" },
  { tab: "foto-rebeca.png", name: "Rebeca" },
  { tab: "foto-maya-cachorra-pt.jpg", name: "Maya" },
  { tab: "foto-abigail.png", name: "Abigail" },
  { tab: "foto-nanoaventuras.jpg", name: "Nano" },
  { tab: "foto-miriam.png", name: "Miriam" },
  { tab: "foto-mako-amigofiel.jpg", name: "Mako" },
  { tab: "foto-noe.png", name: "Noé" },
] as const;
type CatalogImg = string | Record<Lang, string>;
function catalogImgSrc(img: CatalogImg, lang: Lang): string {
  return typeof img === "string" ? img : img[lang];
}
const CATALOG_IMGS: CatalogImg[] = [
  "capa-martin-goleiro.jpg",
  "capa-emilia-bailarina.jpg",
  "capa-antonio-bicicleta.jpg",
  "capa-sofia-alfabeto.png",
  { pt: "capa-bruno-animais.png", en: "capa-bruno-animais-en.png", es: "capa-bruno-animais-es.png" },
  "capa-cristobal-esporte.png",
  "capa-nicolas-maefilho.png",
  { pt: "capa-amordemae.png", en: "capa-amordemae-en.png", es: "capa-amordemae-es.png" },
  { pt: "capa-mamaepapaimatteo.png", en: "capa-mamaepapaimatteo-en.png", es: "capa-mamaepapaimatteo-es.png" },
  { pt: "capa-amordebisavo.png", en: "capa-amordebisavo-en.png", es: "capa-amordebisavo-es.png" },
  { pt: "capa-natalmemetata.jpg", en: "capa-natalmemetata-en.jpg", es: "capa-natalmemetata-es.jpg" },
  { pt: "capa-nanoaventuras.png", en: "capa-nanoaventuras-en.png", es: "capa-nanoaventuras-es.png" },
  { pt: "capa-maya-cachorra-pt.jpg", en: "capa-maya-cachorra-en.jpg", es: "capa-maya-cachorra-es.jpg" },
  { pt: "capa-mako-amigofiel.jpg", en: "capa-mako-amigofiel-en.jpg", es: "capa-mako-amigofiel-es.jpg" },
  { pt: "capa-ester.png", en: "capa-ester-en.png", es: "capa-ester-es.png" },
  { pt: "capa-raquel-papai.png", en: "capa-raquel-papai-en.png", es: "capa-raquel-papai-es.png" },
  { pt: "capa-rebeca.png", en: "capa-rebeca-en.png", es: "capa-rebeca-es.png" },
  { pt: "capa-abigail.png", en: "capa-abigail-en.png", es: "capa-abigail-es.png" },
  { pt: "capa-miriam.png", en: "capa-miriam-en.png", es: "capa-miriam-es.png" },
  { pt: "capa-noe.png", en: "capa-noe-en.png", es: "capa-noe-es.png" },
];
const CATALOG_THEMES = [
  "adventure",
  "princess",
  "adventure",
  "alfabetizacao_inicial",
  "animais_sons",
  "sport",
  "mothers_day",
  "mothers_day",
  "family_love",
  "grandparents_love",
  "christmas",
  "adventure",
  "pets",
  "pets",
  "birthday",
  "fathers_day",
  "superhero",
  "space",
  "underwater",
  "dinosaurs",
];
/** Catálogo da principal: no máximo 15, todos com a mesma capa, tamanho e preço. */
const CATALOG_LIMIT = 15;
/** Catálogo do /cartoon: só capas com visual de desenho. */
const CATALOG_DRAWING: { img: string; theme: string; t: Record<Lang, string> }[] = [
  {
    img: "capa-floresta.jpg",
    theme: "fantasy",
    t: { pt: "Floresta Encantada", en: "Enchanted Forest", es: "Bosque Encantado" },
  },
  {
    img: "capa-dino2.jpg",
    theme: "dinosaurs",
    t: { pt: "Mundo dos Dinossauros", en: "Dinosaur World", es: "Mundo de los Dinosaurios" },
  },
  {
    img: "capa-circo.jpg",
    theme: "adventure",
    t: { pt: "No Circo", en: "At the Circus", es: "En el Circo" },
  },
  {
    img: "capa-oceano.jpg",
    theme: "underwater",
    t: { pt: "Fundo do Mar", en: "Under the Sea", es: "Fondo del Mar" },
  },
  {
    img: "capa-amazonia.jpg",
    theme: "adventure",
    t: { pt: "Amazônia", en: "The Amazon", es: "La Amazonía" },
  },
];
const CATALOG_DESC: Record<Lang, string> = {
  pt: "Capa dura ou mole, 15 × 15 cm ou 20 × 20 cm. 16 páginas.",
  en: "Hardcover or softcover, 15 × 15 cm or 20 × 20 cm. 16 pages.",
  es: "Tapa dura o blanda, 15 × 15 cm o 20 × 20 cm. 16 páginas.",
};
const CATALOG_PRICE: Record<Lang, string> = {
  pt: "Sob consulta",
  en: "On request",
  es: "Bajo consulta",
};
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
      { href: "/app?tema=sport" },
    ],
    feats: [
      { href: "/app?tema=princess", catalogI: 1 },
      { href: "/app?tema=adventure", catalogI: 0 },
      { href: "/app?tema=sport", catalogI: 5 },
      { href: "/app?tema=adventure", catalogI: 11 },
    ],
  },
  {
    color: "#b48ad4",
    subs: [
      { href: "/app?tema=mothers_day" },
      { href: "/app?tema=fathers_day" },
      { href: "/app?tema=grandparents_love" },
      { href: "/app?tema=family_love" },
      { href: "/app" },
    ],
    feats: [
      { href: "/app?tema=mothers_day", catalogI: 6 },
      { href: "/app?tema=grandparents_love", catalogI: 9 },
      { href: "/app?tema=family_love", catalogI: 8 },
      { href: "/app?tema=mothers_day", catalogI: 7 },
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
      { href: "/app?tema=christmas", catalogI: 10 },
      { href: "/app?tema=mothers_day", catalogI: 6 },
      { href: "/app?tema=mothers_day", catalogI: 7 },
      { href: "/app?tema=birthday", catalogI: 14 },
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
      { href: "/app?tema=alfabetizacao_inicial", catalogI: 3 },
      { href: "/app?tema=animais_sons", catalogI: 4 },
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
    feats: [],
  },
] as const;
const exUrl = (f: string) => (f.startsWith("http://") || f.startsWith("https://") ? f : `${import.meta.env.BASE_URL}exemplos/${f}`);

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

const I18N = {
  pt: {
    nav: ["Como funciona", "Livros", "Vídeos", "FAQ"],
    reviews_link: "Avaliações",
    videos_link: "Vídeos",
    my_books: "Meus Livros",
    our_story: "Cartoon",
    see_all_books: "Ver todos os livros",
    view_all: "Ver todos",
    cats_label: "Categorias",
    quick_links: "Acessos rápidos",
    font_label: "Fonte do título",
    explore: "Explorar agora",
    eyebrow: "Eternize momentos. Presenteie familiares com uma história inesquecível.",
    h_pre: "Transforme uma foto em uma ", w1: "história inesquecível", c1: ", onde seu filho é o ", w2: "protagonista", h_suf: " !",
    lead: "Você envia a foto e nós transformamos seu filho em um personagem ilustrado, criando uma aventura personalizada especialmente para ele — um livro para presentear a família e guardar para sempre.",
    cta_play: "Criar minha conta",
    hero_cta: "Criar meu livro",
    cta_story: "Criar minha história",
    hero_sign: "Uma foto. Uma história. Uma memória eterna.",
    cats: [
      {
        name: "Aventuras",
        subs: ["Aventura", "Fantasia", "Dinossauros", "Fundo do mar", "Espaço", "Princesas", "Super-heróis", "Esportes"],
        feats: ["Princesas", "Aventura", "Cristobal e seu Esporte Favorito", "Nano e suas Aventuras"],
      },
      {
        name: "Você e Eu",
        subs: ["Mamãe e Eu", "Papai e Eu", "Vovó e Vovô", "Nossa Família", "Irmãos e primos"],
        feats: ["Mamãe e Eu", "Vovó e Vovô", "Nossa Família", "O Amor de Mãe"],
      },
      {
        name: "Ocasiões Especiais",
        subs: ["Natal", "Aniversário", "Dia das Mães", "Dia dos Pais", "Páscoa", "Dia das Crianças", "Ano Novo"],
        feats: ["Natal", "Dia das Mães", "O Amor de Mãe", "O Aniversário Especial de Ester"],
      },
      {
        name: "Educativo",
        subs: ["Alfabetização", "Matemática", "Cores", "Higiene", "Vestir-se", "Animais", "Transporte"],
        feats: ["Alfabetização", "Animais"],
      },
      {
        name: "Sentimentos",
        subs: ["Sentimentos", "Hora de Dormir", "Compartilhar", "Corpo"],
        feats: [],
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
    hiw_title: "Como funciona", hiw_sub: "Você manda as fotos. A gente faz o livro, com seu filho como personagem.",
    hiw: [
      { t: "Envie as fotos", p: "Da criança e de quem entra na história." },
      { t: "A gente cria o livro", p: "Um personagem parecido com a foto e uma história só de vocês." },
      { t: "O livro fica pronto", p: "Páginas ilustradas para ler e guardar." },
    ],
    shot_sub: "Fotos nítidas deixam o personagem mais parecido.",
    shots: [
      { t: "A criança", p: "3 a 5 fotos recentes, de frente e com boa luz. Sem filtro, chapéu ou óculos escuros." },
      { t: "Família e pets", p: "Cada pessoa: 2 ou 3 fotos sozinha. O pet: de frente e de corpo inteiro." },
      { t: "O que contar", p: "Nome, idade, tema do livro e idioma." },
    ],
    shot_title: "Dicas para a foto perfeita",
    cartoon_shot_sub: "Envie uma foto nítida da criança, com o rosto centralizado.",
    cartoon_shots: ["Nítida, bem iluminada e centralizada", "Mais de uma pessoa na foto", "Rosto de lado"],
    cartoon_hiw_title: "Você envia a foto",
    cartoon_hiw_photo: "Uma foto da criança já basta para começar.",
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
    cat_title: "Nossos livros", cat_sub: "Cada tema se transforma em uma narrativa ilustrada, concebida para que seu filho seja o protagonista de sua própria história.",
    personalize: "Personalizar",
    a11y_theme: "Alternar tema claro/escuro",
    a11y_menu: "Menu",
    a11y_slide: "Slide",
    photo_real_alt: "Foto de exemplo da criança",
    fb_prev: "Página anterior",
    fb_next: "Próxima página",
    fb_turn: "Virar página",
    fb_cover: "Capa",
    fb_photo: "Na mão",
    theme_to_light: "Claro",
    theme_to_dark: "Escuro",
    privacy_link: "Privacidade",
    terms_link: "Termos",
    catalog: [
      { t: "Martin, o Grande Goleiro do Chile", p: "Goleiro que cai, levanta e defende: coragem e perseverança no campo.", cover: "Hard", size: "M", tag: "Esporte e coragem", quote: "Cair, levantar e continuar!" },
      { t: "Emilia e os Primeiros Passos da Bailarina", p: "Primeiros passos no ballet com disciplina, equilíbrio e confiança.", cover: "Soft", size: "M", tag: "Ballet e sonhos", quote: "Pequenos passos, grandes conquistas." },
      { t: "Antonio e sua Bicicleta", p: "Pedalar, aprender e explorar o mundo em pequenas aventuras.", cover: "Soft", size: "M", tag: "Aventura e movimento", quote: "Pedalar, aprender e sorrir!" },
      { t: "Aprendendo o Alfabeto com a Sofia", p: "Letras e descobertas na floresta, alfabetizar brincando.", cover: "Soft", size: "M", tag: "Alfabetizar brincando", quote: "Cada letra abre um mundo novo." },
      { t: "Bruno em uma aventura animal", p: "Conhecer animais e cuidar da natureza numa jornada gentil.", cover: "Soft", size: "M", tag: "Animais e natureza", quote: "Cada animal é especial — e juntos cuidamos do mundo." },
      { t: "Cristobal e seu Esporte Favorito", p: "No caiaque, equilíbrio, coragem e respeito pelo rio.", cover: "Hard", size: "M", tag: "Esporte e coragem", quote: "Pequenas remadas, grandes conquistas." },
      { t: "Nicolas, Meu Primeiro Amor", p: "Um momento de carinho eterno entre mamãe e filho, cheio de ternura para guardar para sempre.", cover: "Soft", size: "M", tag: "Amor de mãe", quote: "Primeiro filho, eterno amor!" },
      { t: "O Amor de Mãe", p: "Pequenas histórias de um grande amor: a ternura da mamãe em cada página, para guardar para sempre.", cover: "Hard", size: "M", tag: "Amor de mãe", quote: "No colo da mamãe, encontro meu lugar." },
      { t: "Mamãe, Papai e Matteo", p: "Uma celebração da família: o carinho de mamãe e papai unidos em uma história só deles.", cover: "Hard", size: "M", tag: "Amor de família", quote: "Juntos, fazemos do amor o nosso lar." },
      { t: "Amor de Bisavó", p: "Uma homenagem à bisavó: colo, carinho e histórias que atravessam gerações, para guardar para sempre.", cover: "Hard", size: "M", tag: "Amor entre gerações", quote: "Bisavó tem abraço que acolhe e guarda todo o meu carinho." },
      { t: "Natal com a Meme e o Tata", p: "Um Natal em família: o carinho da Meme e do Tata, luzes na árvore e um abraço apertado para guardar para sempre.", cover: "Hard", size: "M", tag: "Natal em família", quote: "Natal é mais gostoso ao lado de quem a gente ama." },
      { t: "Nano e suas Aventuras", p: "Uma aventura marítima só dele: vento nas orelhas, mar azul e a alegria de explorar ao lado de quem ama, para guardar para sempre.", cover: "Hard", size: "M", tag: "Aventura e mar", quote: "Vento nas orelhas, mar pela frente — a aventura começou!" },
      { t: "Maya, Minha Cachorra Carinhosa", p: "Uma amizade cheia de carinho entre uma menina e sua cadela: cuidado, afeto e companhia em cada página.", cover: "Soft", size: "M", tag: "Amizade e cuidado", quote: "Amor e cuidado, todos os dias." },
      { t: "Mako, Meu Amigo Fiel", p: "Um bebê e seu cão fiel: lealdade, proteção e carinho em uma amizade só deles.", cover: "Soft", size: "M", tag: "Amizade e lealdade", quote: "Amor fiel, todos os dias." },
      { t: "O Aniversário Especial de Ester", p: "Velas, abraços e um pedido no coração: o aniversário do seu filho vira uma história só dele.", cover: "Hard", size: "M", tag: "Aniversário", quote: "Mais um ano de felicidade!" },
      { t: "Raquel e Papai: Aventuras para Sempre", p: "Mão na mão com o papai, cada caminho vira memória — uma aventura para guardar para sempre.", cover: "Hard", size: "M", tag: "Papai e eu", quote: "Juntos, a aventura nunca acaba." },
      { t: "Rebeca, a Pequena Grande Heroína", p: "Capa ao vento e coragem no peito: o seu filho salva o dia com o coração.", cover: "Hard", size: "M", tag: "Super-heróis", quote: "Ser herói começa com um sorriso." },
      { t: "Abigail em uma Aventura pelo Espaço", p: "Foguetes, planetas e curiosidade: uma viagem estelar com o seu filho no comando.", cover: "Hard", size: "M", tag: "Espaço", quote: "Coragem, curiosidade e descobertas!" },
      { t: "Miriam e os Segredos do Fundo do Mar", p: "Tartarugas, corais e amizade: o seu filho explora o oceano com cuidado e encanto.", cover: "Hard", size: "M", tag: "Fundo do mar", quote: "Cuidar do mar é cuidar dos amigos." },
      { t: "Noé na Terra dos Dinossauros", p: "Fósseis, amigos gigantes e coragem: uma expedição pré-histórica com o seu filho.", cover: "Hard", size: "M", tag: "Dinossauros", quote: "Descobrir juntos é a melhor aventura." },
    ],
    promise_title: "Um presente personalizado para eternizar momentos inesquecíveis.",
    promise_sub: "Da foto à prévia final, cada detalhe é criado com carinho, dando vida a um presente único para toda a vida.",
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
    videos_link: "Videos",
    my_books: "My Books",
    our_story: "Cartoon",
    see_all_books: "See all books",
    view_all: "View all",
    cats_label: "Categories",
    quick_links: "Quick links",
    font_label: "Cover font",
    explore: "Explore now",
    eyebrow: "Preserve moments. Gift your family an unforgettable story.",
    h_pre: "Turn a photo into an ", w1: "unforgettable story", c1: ", where your child is the ", w2: "hero", h_suf: " !",
    lead: "You send the photo and we turn your child into an illustrated character, creating an adventure made just for them — a book to gift the family and keep forever.",
    cta_play: "Create my account",
    hero_cta: "Create my book",
    cta_story: "Create my story",
    hero_sign: "One photo. One story. One lasting memory.",
    cats: [
      {
        name: "Adventures",
        subs: ["Adventure", "Fantasy", "Dinosaurs", "Under the sea", "Space", "Princesses", "Superheroes", "Sports"],
        feats: ["Princesses", "Adventure", "Cristobal and His Favorite Sport", "Nano and His Adventures"],
      },
      {
        name: "You and Me",
        subs: ["Mommy and Me", "Daddy and Me", "Grandma and Grandpa", "Our Family", "Siblings and cousins"],
        feats: ["Mommy and Me", "Grandma and Grandpa", "Our Family", "A Mother's Love"],
      },
      {
        name: "Special Occasions",
        subs: ["Christmas", "Birthday", "Mother's Day", "Father's Day", "Easter", "Children's Day", "New Year"],
        feats: ["Christmas", "Mother's Day", "A Mother's Love", "Ester's Special Birthday"],
      },
      {
        name: "Educational",
        subs: ["Literacy", "Math", "Colors", "Hygiene", "Getting dressed", "Animals", "Transport"],
        feats: ["Literacy", "Animals"],
      },
      {
        name: "Feelings",
        subs: ["Feelings", "Bedtime", "Sharing", "Body"],
        feats: [],
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
    hiw_title: "How it works", hiw_sub: "You send the photos. We make the book, with your child as the character.",
    hiw: [
      { t: "Send the photos", p: "Of your child and anyone else in the story." },
      { t: "We make the book", p: "A character that looks like the photo, and a story just for you." },
      { t: "The book is ready", p: "Illustrated pages to read and keep." },
    ],
    shot_sub: "Clear photos make the character look more like your child.",
    shots: [
      { t: "The child", p: "3 to 5 recent photos, facing the camera, in good light. No filters, hats, or sunglasses." },
      { t: "Family and pets", p: "Each person: 2 or 3 photos alone. Pets: front and full body." },
      { t: "What to tell us", p: "Name, age, book theme, and language." },
    ],
    shot_title: "Tips for the perfect photo",
    cartoon_shot_sub: "Upload a clear photo of your child with the face centered.",
    cartoon_shots: ["Clear, well-lit and centered", "More than one person in the photo", "Face at an angle"],
    cartoon_hiw_title: "You send the photo",
    cartoon_hiw_photo: "One photo of your child is all it takes to begin.",
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
    cat_title: "Our books", cat_sub: "Each theme becomes an illustrated narrative, designed so your child is the hero of their own story.",
    personalize: "Personalize",
    a11y_theme: "Toggle light/dark theme",
    a11y_menu: "Menu",
    a11y_slide: "Slide",
    photo_real_alt: "Example photo of the child",
    fb_prev: "Previous page",
    fb_next: "Next page",
    fb_turn: "Turn page",
    fb_cover: "Cover",
    fb_photo: "In hand",
    theme_to_light: "Light",
    theme_to_dark: "Dark",
    privacy_link: "Privacy",
    terms_link: "Terms",
    catalog: [
      { t: "Martin, the Great Goalkeeper of Chile", p: "A goalkeeper who falls, rises and defends: courage and grit on the field.", cover: "Hard", size: "M", tag: "Sport and courage", quote: "Fall, rise, and keep going!" },
      { t: "Emilia and the Ballerina's First Steps", p: "Ballet's first steps with discipline, balance and confidence.", cover: "Soft", size: "M", tag: "Ballet and dreams", quote: "Small steps, big achievements." },
      { t: "Antonio and His Bicycle", p: "Pedal, learn and explore the world in small adventures.", cover: "Soft", size: "M", tag: "Adventure and movement", quote: "Pedal, learn and smile!" },
      { t: "Learning the Alphabet with Sofia", p: "Letters and forest discoveries — literacy through play.", cover: "Soft", size: "M", tag: "Literacy through play", quote: "Every letter opens a new world." },
      { t: "Bruno on an Animal Adventure", p: "Meet animals and care for nature on a gentle journey.", cover: "Soft", size: "M", tag: "Animals and nature", quote: "Every animal is special — and together we care for the world." },
      { t: "Cristobal and His Favorite Sport", p: "On the kayak: balance, courage and respect for the river.", cover: "Hard", size: "M", tag: "Sport and courage", quote: "Small paddles, big victories." },
      { t: "Nicolas, My First Love", p: "A tender, eternal moment between mom and son, full of warmth to treasure forever.", cover: "Soft", size: "M", tag: "A mother's love", quote: "First child, eternal love!" },
      { t: "A Mother's Love", p: "Small stories of a big love: mom's tenderness on every page, to treasure forever.", cover: "Hard", size: "M", tag: "A mother's love", quote: "In mom's arms, I find my place." },
      { t: "Mommy, Daddy and Matteo", p: "A celebration of family: mom and dad's love coming together in a story all their own.", cover: "Hard", size: "M", tag: "Family love", quote: "Together, we make love our home." },
      { t: "A Great-Grandmother's Love", p: "A tribute to great-grandma: hugs, warmth and stories that cross generations, to treasure forever.", cover: "Hard", size: "M", tag: "Love across generations", quote: "Great-grandma's hug holds all my love." },
      { t: "Christmas with Tata and Meme", p: "A family Christmas: the warmth of grandma and grandpa, twinkling lights and a big hug to treasure forever.", cover: "Hard", size: "M", tag: "Family Christmas", quote: "Christmas feels warmer with the ones we love." },
      { t: "Nano and His Adventures", p: "A sea adventure all his own: the wind in his ears, the blue ocean and the joy of exploring beside the ones he loves, to treasure forever.", cover: "Hard", size: "M", tag: "Adventure and sea", quote: "Wind in his ears, sea ahead — the adventure has begun!" },
      { t: "Maya, My Loving Dog", p: "A heartwarming friendship between a girl and her dog: care, affection and companionship on every page.", cover: "Soft", size: "M", tag: "Friendship and care", quote: "Love and care, every day." },
      { t: "Mako, My Loyal Friend", p: "A baby and his loyal dog: loyalty, protection and affection in a friendship all their own.", cover: "Soft", size: "M", tag: "Friendship and loyalty", quote: "Loyal love, every day." },
      { t: "Ester's Special Birthday", p: "Candles, hugs and a wish from the heart: your child's birthday becomes a story all their own.", cover: "Hard", size: "M", tag: "Birthday", quote: "One more year of happiness!" },
      { t: "Raquel and Dad: Adventures Forever", p: "Hand in hand with dad, every path becomes a memory — an adventure to keep forever.", cover: "Hard", size: "M", tag: "Dad and me", quote: "Together, the adventure never ends." },
      { t: "Rebeca, the Little Great Heroine", p: "Cape in the wind and courage in her heart: your child saves the day with kindness.", cover: "Hard", size: "M", tag: "Superheroes", quote: "Being a hero starts with a smile." },
      { t: "Abigail on a Space Adventure", p: "Rockets, planets and curiosity: a starry journey with your child at the helm.", cover: "Hard", size: "M", tag: "Space", quote: "Courage, curiosity and discovery!" },
      { t: "Miriam and the Secrets of the Deep Sea", p: "Turtles, coral and friendship: your child explores the ocean with care and wonder.", cover: "Hard", size: "M", tag: "Under the sea", quote: "Caring for the sea is caring for friends." },
      { t: "Noé in the Land of Dinosaurs", p: "Fossils, giant friends and courage: a prehistoric expedition with your child.", cover: "Hard", size: "M", tag: "Dinosaurs", quote: "Discovering together is the best adventure." },
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
    videos_link: "Videos",
    my_books: "Mis Libros",
    our_story: "Cartoon",
    see_all_books: "Ver todos los libros",
    view_all: "Ver todos",
    cats_label: "Categorías",
    quick_links: "Accesos rápidos",
    font_label: "Fuente del título",
    explore: "Explorar ahora",
    eyebrow: "Eterniza momentos. Regala a tu familia una historia inolvidable.",
    h_pre: "Convierte una foto en una ", w1: "historia inolvidable", c1: ", donde tu hijo es el ", w2: "protagonista", h_suf: " !",
    lead: "Envías la foto y transformamos a tu hijo en un personaje ilustrado, creando una aventura personalizada especialmente para él — un libro para regalar a la familia y guardar para siempre.",
    cta_play: "Crear mi cuenta",
    hero_cta: "Crear mi libro",
    cta_story: "Crear mi historia",
    hero_sign: "Una foto. Una historia. Una memoria eterna.",
    cats: [
      {
        name: "Aventuras",
        subs: ["Aventura", "Fantasía", "Dinosaurios", "Fondo del mar", "Espacio", "Princesas", "Superhéroes", "Deportes"],
        feats: ["Princesas", "Aventura", "Cristobal y su deporte favorito", "Nano y sus aventuras"],
      },
      {
        name: "Tú y Yo",
        subs: ["Mamá y Yo", "Papá y Yo", "Abuela y Abuelo", "Nuestra Familia", "Hermanos y primos"],
        feats: ["Mamá y Yo", "Abuela y Abuelo", "Nuestra Familia", "El Amor de Mamá"],
      },
      {
        name: "Ocasiones Especiales",
        subs: ["Navidad", "Cumpleaños", "Día de la Madre", "Día del Padre", "Pascua", "Día del Niño", "Año Nuevo"],
        feats: ["Navidad", "Día de la Madre", "El Amor de Mamá", "El Cumpleaños Especial de Ester"],
      },
      {
        name: "Educativo",
        subs: ["Alfabetización", "Matemáticas", "Colores", "Higiene", "Vestirse", "Animales", "Transporte"],
        feats: ["Alfabetización", "Animales"],
      },
      {
        name: "Sentimientos",
        subs: ["Sentimientos", "Hora de Dormir", "Compartir", "Cuerpo"],
        feats: [],
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
    hiw_title: "Cómo funciona", hiw_sub: "Tú envías las fotos. Nosotros hacemos el libro, con tu hijo como personaje.",
    hiw: [
      { t: "Envía las fotos", p: "Del niño y de quien más entra en la historia." },
      { t: "Creamos el libro", p: "Un personaje parecido a la foto y una historia solo de ustedes." },
      { t: "El libro queda listo", p: "Páginas ilustradas para leer y guardar." },
    ],
    shot_sub: "Fotos nítidas hacen que el personaje se parezca más.",
    shots: [
      { t: "El niño", p: "De 3 a 5 fotos recientes, de frente y con buena luz. Sin filtro, sombrero ni gafas de sol." },
      { t: "Familia y mascotas", p: "Cada persona: 2 o 3 fotos sola. La mascota: de frente y de cuerpo entero." },
      { t: "Qué contarnos", p: "Nombre, edad, tema del libro e idioma." },
    ],
    shot_title: "Consejos para la foto perfecta",
    cartoon_shot_sub: "Envía una foto nítida del niño, con el rostro centrado.",
    cartoon_shots: ["Nítida, bien iluminada y centrada", "Más de una persona en la foto", "Rostro de lado"],
    cartoon_hiw_title: "Tú envías la foto",
    cartoon_hiw_photo: "Una foto del niño ya basta para empezar.",
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
    cat_title: "Nuestros libros", cat_sub: "Cada tema se transforma en una narrativa ilustrada, concebida para que tu hijo sea el protagonista de su propia historia.",
    personalize: "Personalizar",
    a11y_theme: "Cambiar tema claro/oscuro",
    a11y_menu: "Menú",
    a11y_slide: "Diapositiva",
    photo_real_alt: "Foto de ejemplo del niño",
    fb_prev: "Página anterior",
    fb_next: "Página siguiente",
    fb_turn: "Pasar página",
    fb_cover: "Portada",
    fb_photo: "En manos",
    theme_to_light: "Claro",
    theme_to_dark: "Oscuro",
    privacy_link: "Privacidad",
    terms_link: "Términos",
    catalog: [
      { t: "Martin, el gran arquero de Chile", p: "Arquero que cae, se levanta y defiende: coraje y perseverancia en el campo.", cover: "Hard", size: "M", tag: "Deporte y coraje", quote: "¡Caer, levantarse y seguir!" },
      { t: "Emilia y los primeros pasos de la bailarina", p: "Primeros pasos en el ballet con disciplina, equilibrio y confianza.", cover: "Soft", size: "M", tag: "Ballet y sueños", quote: "Pequeños pasos, grandes logros." },
      { t: "Antonio y su bicicleta", p: "Pedalear, aprender y explorar el mundo en pequeñas aventuras.", cover: "Soft", size: "M", tag: "Aventura y movimiento", quote: "¡Pedalear, aprender y sonreír!" },
      { t: "Aprendiendo el alfabeto con Sofia", p: "Letras y descubrimientos en el bosque, alfabetizar jugando.", cover: "Soft", size: "M", tag: "Alfabetizar jugando", quote: "Cada letra abre un mundo nuevo." },
      { t: "Bruno en una aventura animal", p: "Conocer animales y cuidar la naturaleza en una jornada gentil.", cover: "Soft", size: "M", tag: "Animales y naturaleza", quote: "Cada animal es especial — y juntos cuidamos el mundo." },
      { t: "Cristobal y su deporte favorito", p: "En el kayak: equilibrio, coraje y respeto por el río.", cover: "Hard", size: "M", tag: "Deporte y coraje", quote: "Pequeñas paladas, grandes conquistas." },
      { t: "Nicolas, Mi Primer Amor", p: "Un momento de cariño eterno entre mamá e hijo, lleno de ternura para guardar para siempre.", cover: "Soft", size: "M", tag: "Amor de madre", quote: "¡Primer hijo, amor eterno!" },
      { t: "El Amor de Mamá", p: "Pequeñas historias de un gran amor: la ternura de mamá en cada página, para guardar para siempre.", cover: "Hard", size: "M", tag: "Amor de madre", quote: "En los brazos de mamá, encuentro mi lugar." },
      { t: "Mamá, Papá y Matteo", p: "Una celebración de la familia: el cariño de mamá y papá unidos en una historia solo de ellos.", cover: "Hard", size: "M", tag: "Amor de familia", quote: "Juntos, hacemos del amor nuestro hogar." },
      { t: "Amor de Bisabuela", p: "Un homenaje a la bisabuela: abrazos, cariño e historias que atraviesan generaciones, para guardar para siempre.", cover: "Hard", size: "M", tag: "Amor entre generaciones", quote: "El abrazo de la bisabuela guarda todo mi cariño." },
      { t: "Navidad con Tata y Meme", p: "Una Navidad en familia: el cariño de la Meme y el Tata, luces en el árbol y un abrazo apretado para guardar para siempre.", cover: "Hard", size: "M", tag: "Navidad en familia", quote: "La Navidad es más linda junto a quienes amamos." },
      { t: "Nano y sus Aventuras", p: "Una aventura marítima solo para él: viento en las orejas, mar azul y la alegría de explorar junto a quienes ama, para guardar para siempre.", cover: "Hard", size: "M", tag: "Aventura y mar", quote: "Viento en las orejas, mar por delante — ¡la aventura comenzó!" },
      { t: "Maya, Mi Perrita Cariñosa", p: "Una amistad llena de cariño entre una niña y su perrita: cuidado, afecto y compañía en cada página.", cover: "Soft", size: "M", tag: "Amistad y cuidado", quote: "Amor y cuidado, todos los días." },
      { t: "Mako, Mi Amigo Fiel", p: "Un bebé y su perro fiel: lealtad, protección y cariño en una amistad solo de ellos.", cover: "Soft", size: "M", tag: "Amistad y lealtad", quote: "Amor fiel, todos los días." },
      { t: "El Cumpleaños Especial de Ester", p: "Velas, abrazos y un deseo en el corazón: el cumpleaños de tu hijo se vuelve una historia solo de él.", cover: "Hard", size: "M", tag: "Cumpleaños", quote: "¡Un año más de felicidad!" },
      { t: "Raquel y Papá: Aventuras para Siempre", p: "De la mano con papá, cada camino se vuelve recuerdo — una aventura para guardar para siempre.", cover: "Hard", size: "M", tag: "Papá y yo", quote: "Juntos, la aventura nunca termina." },
      { t: "Rebeca, la Pequeña Gran Heroína", p: "Capa al viento y coraje en el pecho: tu hijo salva el día con el corazón.", cover: "Hard", size: "M", tag: "Superhéroes", quote: "Ser héroe empieza con una sonrisa." },
      { t: "Abigail en una Aventura por el Espacio", p: "Cohetes, planetas y curiosidad: un viaje estelar con tu hijo al mando.", cover: "Hard", size: "M", tag: "Espacio", quote: "¡Coraje, curiosidad y descubrimientos!" },
      { t: "Miriam y los Secretos del Fondo del Mar", p: "Tortugas, corales y amistad: tu hijo explora el océano con cuidado y encanto.", cover: "Hard", size: "M", tag: "Fondo del mar", quote: "Cuidar el mar es cuidar a los amigos." },
      { t: "Noé en la Tierra de los Dinosaurios", p: "Fósiles, amigos gigantes y coraje: una expedición prehistórica con tu hijo.", cover: "Hard", size: "M", tag: "Dinosaurios", quote: "Descubrir juntos es la mejor aventura." },
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

const FLIP_MS = 600;

function FlipBook({
  pages,
  index,
  onIndex,
  labels,
}: {
  pages: string[];
  index: number;
  onIndex: (next: number) => void;
  labels: { prev: string; next: string; turn: string; cover: string; photo: string };
}) {
  const [anim, setAnim] = useState<"next" | "prev" | null>(null);
  const [target, setTarget] = useState(index);
  const [frame, setFrame] = useState<{ w: number; h: number } | null>(null);
  const busy = useRef(false);
  const pageSrc = pages[index];
  useEffect(() => {
    const img = new Image();
    let alive = true;
    const apply = () => {
      if (!alive || !img.naturalWidth || !img.naturalHeight) return;
      const maxW = Math.max(240, Math.min(img.naturalWidth, window.innerWidth - 160));
      const maxH = Math.max(180, Math.min(img.naturalHeight, window.innerHeight * 0.72));
      const scale = Math.min(maxW / img.naturalWidth, maxH / img.naturalHeight);
      setFrame({
        w: Math.round(img.naturalWidth * scale),
        h: Math.round(img.naturalHeight * scale),
      });
    };
    img.onload = apply;
    img.src = exUrl(pageSrc);
    if (img.complete) apply();
    window.addEventListener("resize", apply);
    return () => {
      alive = false;
      window.removeEventListener("resize", apply);
    };
  }, [pageSrc]);
  const flip = (dir: "next" | "prev") => {
    if (busy.current || pages.length < 2) return;
    const t = dir === "next" ? index + 1 : index - 1;
    if (t < 0 || t >= pages.length) return;
    busy.current = true;
    setTarget(t);
    setAnim(dir);
    window.setTimeout(() => {
      onIndex(t);
      setAnim(null);
      busy.current = false;
    }, FLIP_MS);
  };
  const underSrc = anim === "next" ? pages[target] : pages[index];
  const leafSrc = anim === "next" ? pages[index] : (anim === "prev" ? pages[target] : pages[index]);
  const underIdx = anim === "next" ? target : index;
  const leafIdx = anim === "next" ? index : (anim === "prev" ? target : index);
  const pageKind = (idx: number) => {
    if (idx === 0) return "fb-page--cover";
    if (idx === pages.length - 1) return "fb-page--photo";
    return "fb-page--spread";
  };
  const pageLabel = (idx: number) => {
    if (idx === 0) return labels.cover;
    if (idx === pages.length - 1) return labels.photo;
    return `${idx} / ${Math.max(pages.length - 2, 1)}`;
  };
  const single = pages.length < 2;
  const onStage = (e: RMouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (e.clientX - r.left > r.width / 2) flip("next"); else flip("prev");
  };
  const onStageKey = (e: RKeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") {
      e.preventDefault();
      flip("next");
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      flip("prev");
    }
  };
  return (
    <div className="flipbook">
      {single ? null : <button className="fb-nav" type="button" onClick={() => flip("prev")} disabled={index === 0 || !!anim} aria-label={labels.prev}>‹</button>}
      <div
        className="fb-stage"
        onClick={single ? undefined : onStage}
        onKeyDown={single ? undefined : onStageKey}
        role={single ? "img" : "button"}
        tabIndex={single ? undefined : 0}
        aria-label={single ? pageLabel(index) : labels.turn}
        style={frame ? { width: frame.w, height: "auto", aspectRatio: `${frame.w} / ${frame.h}`, maxWidth: "100%" } : undefined}
      >
        <span className="fb-spine" />
        <img className={`fb-page fb-under ${pageKind(underIdx)}`} src={exUrl(underSrc)} alt="" aria-hidden />
        <div className={`fb-leaf${anim ? ` ${anim}` : ""}`}>
          <img className={`fb-page ${pageKind(leafIdx)}`} src={exUrl(leafSrc)} alt={pageLabel(index)} data-testid="landing-hero-flip" />
        </div>
      </div>
      {single ? null : <button className="fb-nav" type="button" onClick={() => flip("next")} disabled={index === pages.length - 1 || !!anim} aria-label={labels.next}>›</button>}
    </div>
  );
}

export function Landing({ variant = "photo" }: { variant?: "photo" | "cartoon" } = {}) {
  const rootRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
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
  const [heroPick, setHeroPick] = useState(0);
  const [coverFont] = useState<CoverFont>(() => {
    try {
      const s = localStorage.getItem("coverFont");
      if (s === "fredoka" || s === "baloo" || s === "lilita") return s;
    } catch { /* ignore */ }
    return "fredoka";
  });
  const t = I18N[lang];
  const classicHow = variant === "cartoon";
  const hiwSteps = classicHow
    ? t.hiw.map((h, i) => (i === 0 ? { ...h, t: t.cartoon_hiw_title, p: t.cartoon_hiw_photo } : h))
    : t.hiw;
  const navHrefs = ["#como", "#catalogo", "#videos", "#faq"];
  const heroStrip = variant === "cartoon" ? HERO_STRIP_CARTOON : HERO_STRIP;
  const catalogBooks = variant === "cartoon"
    ? CATALOG_DRAWING.map((book) => ({ t: book.t[lang], img: book.img, theme: book.theme }))
    : t.catalog.slice(0, CATALOG_LIMIT).map((c, i) => ({
        t: c.t,
        img: catalogImgSrc(CATALOG_IMGS[i], lang),
        theme: CATALOG_THEMES[i],
      }));
  const heroSlides = heroStrip.flatMap((book) => [
    { src: book.cover[lang], alt: book.name },
    { src: book.page[lang], alt: book.name },
    { src: book.photo[lang], alt: book.name },
  ]);
  const heroSlide = heroSlides[heroPick] ?? heroSlides[0];
  const flipLabels = { prev: t.fb_prev, next: t.fb_next, turn: t.fb_turn, cover: t.fb_cover, photo: t.fb_photo };
  const navCats = t.cats.map((cat, i) => ({
    ...cat,
    color: NAV_CAT_META[i].color,
    subs: cat.subs.map((label, j) => ({ label, href: NAV_CAT_META[i].subs[j].href })),
    feats: cat.feats.map((label, j) => ({
      label,
      href: NAV_CAT_META[i].feats[j].href,
      img: catalogImgSrc(CATALOG_IMGS[NAV_CAT_META[i].feats[j].catalogI], lang),
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
    if (!navOpen && openCat === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setNavOpen(false);
        setMobileCat(null);
        setOpenCat(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navOpen, openCat]);

  useEffect(() => {
    if (openCat === null && !navOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as Node | null;
      if (target && headerRef.current?.contains(target)) return;
      setOpenCat(null);
      setNavOpen(false);
      setMobileCat(null);
    };
    window.addEventListener("pointerdown", onPointerDown);
    return () => window.removeEventListener("pointerdown", onPointerDown);
  }, [navOpen, openCat]);

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

      <header className="khead" ref={headerRef}>
        <div className="khead-inner">
        <a href="#top" className="kbrand" data-testid="landing-brand"><img src={logo} alt="Story.R.Us" /></a>
        <div className="khead-main">
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
                      aria-controls={`cat-panel-${i}`}
                      onClick={() => setOpenCat(openCat === i ? null : i)}
                    >
                      <span className="kcat-dot" style={{ background: cat.color, boxShadow: `0 0 10px ${cat.color}` }} />
                      {cat.name}
                    </button>
                    <div className="kcat-panel" id={`cat-panel-${i}`}>
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
                <a href="#como" className="kcat-btn" onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#7aa2ff", boxShadow: "0 0 10px rgba(122,162,255,.9)" }} />
                  {t.hiw_title}
                </a>
                <a href="#videos" className="kcat-btn" onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#e07a9a", boxShadow: "0 0 10px rgba(224,122,154,.9)" }} />
                  {t.videos_link}
                </a>
                <Link to="/cartoon" className="kcat-btn" onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#5ec4a8", boxShadow: "0 0 10px rgba(94,196,168,.9)" }} />
                  {t.our_story}
                </Link>
                <a href="#reviews" className="kcat-btn" onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#f4b740", boxShadow: "0 0 10px rgba(244,183,64,.95)" }} />
                  {t.reviews_link}
                </a>
              </nav>
            </div>
          </div>
        </div>
        <div className="khead-actions">
          <div className="khead-utils">
            <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t.a11y_theme}>
              {theme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
              <span className="theme-toggle-label">{theme === "dark" ? t.theme_to_light : t.theme_to_dark}</span>
            </button>
            <div className="lang" role="group" aria-label="Idioma / Language / Idioma" data-testid="landing-lang">
              <button className={lang === "pt" ? "on" : ""} onClick={() => setLang("pt")} data-testid="landing-lang-pt">PT</button>
              <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")} data-testid="landing-lang-en">EN</button>
              <button className={lang === "es" ? "on" : ""} onClick={() => setLang("es")} data-testid="landing-lang-es">ES</button>
            </div>
            <div className="khead-links">
              <Link to="/app" className="kbtn kbtn-primary" data-testid="landing-header-cta">{t.cta_play}</Link>
            </div>
          </div>
          <button
            className="khamb"
            aria-label={t.a11y_menu}
            aria-expanded={navOpen}
            aria-controls="site-menu"
            data-testid="landing-menu"
            onClick={() => setNavOpen((v) => !v)}
          >☰</button>
        </div>
        <nav id="site-menu" className={`kmobile${navOpen ? " open" : ""}`} data-testid="landing-site-menu">
          <div className="kmobile-section">
            <p className="kmobile-label">{t.cats_label}</p>
            {navCats.map((cat, i) => (
              <div key={cat.name} className={`kmobile-cat${mobileCat === i ? " open" : ""}`}>
                <button
                  type="button"
                  className="kmobile-cat-btn"
                  aria-expanded={mobileCat === i}
                  aria-controls={`mobile-cat-${i}`}
                  onClick={() => setMobileCat(mobileCat === i ? null : i)}
                >
                  <span className="kcat-dot" style={{ background: cat.color }} />
                  {cat.name}
                  <IcChevron className="faq-chev" />
                </button>
                <div className="kmobile-subs" id={`mobile-cat-${i}`}>
                  <div className="kmobile-subs-inner">
                    {cat.subs.map((sub) => (
                      <Link key={sub.label} to={sub.href} onClick={closeNav}>{sub.label}</Link>
                    ))}
                  </div>
                </div>
              </div>
            ))}
            <Link to="/app" className="kmobile-all" onClick={closeNav}>{t.view_all}</Link>
          </div>
          <div className="kmobile-section">
            <p className="kmobile-label">{t.quick_links}</p>
            <a className="kmobile-link" href="#como" onClick={closeNav}>{t.hiw_title}</a>
            <a className="kmobile-link" href="#videos" onClick={closeNav}>{t.videos_link}</a>
            <Link className="kmobile-link" to="/cartoon" onClick={closeNav}>{t.our_story}</Link>
            <a className="kmobile-link" href="#reviews" onClick={closeNav}>{t.reviews_link}</a>
            <a className="kmobile-link" href="#catalogo" onClick={closeNav}>{t.nav[1]}</a>
            <a className="kmobile-link" href="#faq" onClick={closeNav}>{t.nav[3]}</a>
          </div>
          <Link to="/app" className="kbtn kbtn-primary" data-testid="landing-mobile-cta" onClick={closeNav}>{t.cta_play}</Link>
        </nav>
        </div>
      </header>

      {/* HERO — proposta de valor + faixa de livros */}
      <section className="kbanner-hero" aria-label={t.hero_sign}>
        <div className="khero-intro">
          <h1>{t.h_pre}<em className="g1">{t.w1}</em>{t.c1}<em className="g2">{t.w2}</em>{t.h_suf}</h1>
          <span className="keyebrow"><IcSparkle className="ei" /> {t.hero_sign}</span>
        </div>
        <div className="hero-carousel" aria-label={t.hero_sign}>
          <div className="hero-carousel-track">
            {[0, 1].map((copy) => heroStrip.map((book, seriesIndex) => {
              const shots = [book.cover[lang], book.page[lang], book.photo[lang]];
              const seriesOn = Math.floor(heroPick / 3) === seriesIndex;
              return (
                <div
                  className={`hero-slide${seriesOn ? " on" : ""}`}
                  key={`${copy}-${book.name}-${seriesIndex}`}
                  aria-hidden={copy === 1 ? true : undefined}
                >
                  <span className="hero-slide-frame">
                    {shots.map((src, part) => {
                      const i = seriesIndex * 3 + part;
                      return (
                        <button
                          type="button"
                          className={`hero-shot${i === heroPick ? " on" : ""}`}
                          key={src}
                          aria-pressed={copy === 0 ? i === heroPick : undefined}
                          aria-label={book.name}
                          tabIndex={copy === 1 ? -1 : 0}
                          onClick={() => setHeroPick(i)}
                          data-testid={copy === 0 ? `landing-hero-pick-${i}` : undefined}
                        >
                          <img
                            src={exUrl(src)}
                            alt=""
                            data-testid={copy === 0 ? `landing-hero-slide-${i}` : undefined}
                          />
                        </button>
                      );
                    })}
                  </span>
                </div>
              );
            }))}
          </div>
        </div>
        <div className="khero-flipbook">
          <FlipBook
            key={`${heroSlide.src}-${lang}`}
            pages={[heroSlide.src]}
            index={0}
            onIndex={() => {}}
            labels={flipLabels}
          />
        </div>
        <div className="khero-after">
          <span className="keyebrow"><IcSparkle className="ei" /> {t.eyebrow}</span>
          <Link to="/app" className="kbtn kbtn-primary" data-testid="landing-hero-cta">{t.hero_cta}</Link>
        </div>
      </section>

      {/* COMO FUNCIONA + DICAS */}
      <section className="ksection ksection-como" id="como">
        <div className="como-panel reveal">
          <h2 className="ktitle">{t.hiw_title}</h2>
          <p className="ksub">{t.hiw_sub}</p>
          <div className={`shot-tips${classicHow ? " shot-tips-classic" : ""}`}>
            {classicHow ? (
              <>
                <h3>{t.shot_title}</h3>
                <p className="shot-sub">{t.cartoon_shot_sub}</p>
                <div className="shot-grid">
                  {SHOTS.map((s, i) => (
                    <div className={`shot${s.ok ? " ok" : ""}`} key={t.cartoon_shots[i]}>
                      <div className="shot-ava-wrap">
                        <div className="shot-ava">
                          {s.img ? (
                            <img src={exUrl(s.img)} alt={t.cartoon_shots[i] || t.shot_title} loading="lazy" style={{ objectPosition: s.focus ?? "center center" }} />
                          ) : (
                            <ShotArt kind={s.art ?? "good"} />
                          )}
                        </div>
                        <span className="shot-badge">{s.ok ? <IcCheck /> : <IcClose />}</span>
                      </div>
                      {t.cartoon_shots[i] ? <p>{t.cartoon_shots[i]}</p> : null}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <p className="shot-sub">{t.shot_sub}</p>
                <div className="shot-grid">
                  {t.shots.map((s) => (
                    <article className="shot" key={s.t}>
                      <h3>{s.t}</h3>
                      <p>{s.p}</p>
                    </article>
                  ))}
                </div>
              </>
            )}
          </div>
          <div className="howex">
            {hiwSteps.map((h, i) => (
              <Fragment key={h.t}>
                <figure className={`howex-card${i === 0 ? " howex-card-face" : ""}${i === 1 ? " howex-card-avatar" : ""}${i === 2 ? " howex-card-page" : ""}`}>
                  <div className="howex-media">
                    <img src={exUrl(HOW_IMGS[i])} alt={h.t} loading="lazy" />
                  </div>
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
          {catalogBooks.map((c) => (
            <div className="cat-card reveal" key={c.t} data-testid="landing-catalog-card" data-format="catalog">
              <div className="cat-display">
                <div className="cat-book">
                  <img src={exUrl(c.img)} alt={c.t} loading="lazy" />
                </div>
              </div>
              <div className="cat-body">
                <div className="cat-badges">
                  <span className="cat-price" data-testid="landing-catalog-price">{CATALOG_PRICE[lang]}</span>
                </div>
                <h3>{c.t}</h3>
                <p>{CATALOG_DESC[lang]}</p>
                <Link to={`/app?tema=${c.theme}`} className="kbtn kbtn-primary" data-testid="landing-personalize">{t.personalize}</Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* NOSSA PROMESSA — logo abaixo dos livros */}
      <section className="ksection promise-section" id="promessa">
        <h2 className="ktitle reveal promise-heading">
          {lang === "pt" ? (
            <>
              Um <span className="promise-mark">presente</span> personalizado para eternizar momentos inesquecíveis.
            </>
          ) : t.promise_title}
        </h2>
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
        <div className="rev-carousel reveal" aria-label={t.rev_title}>
          <div className="rev-carousel-track">
            {[0, 1].map((copy) => REVIEW_PHOTOS.map((b, i) => (
              <figure className="rev-photo" key={`${copy}-${b.tab}`} aria-hidden={copy === 1 ? true : undefined}>
                <span className="rev-photo-frame">
                  <img
                    src={exUrl(b.tab)}
                    alt={copy === 0 ? b.name : ""}
                    loading="lazy"
                    data-testid={copy === 0 ? `landing-review-cover-${i}` : undefined}
                  />
                </span>
                <figcaption data-testid={copy === 0 ? `landing-review-name-${i}` : undefined}>{b.name}</figcaption>
              </figure>
            )))}
          </div>
        </div>
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
        <div className="kfoot-links">
          <div className="kfoot-nav">
            {t.nav.map((label, i) => { const Icon = FOOT_ICONS[i]; return (<a key={label} href={navHrefs[i]}><Icon className="ni" />{label}</a>); })}
          </div>
          <div className="kfoot-contacts">
            <a href={`mailto:${CONTACT_EMAIL}`} className="kfoot-contact">
              <IcMail className="ni" />
              <span>{CONTACT_EMAIL}</span>
            </a>
            <a
              href={`https://www.instagram.com/${CONTACT_INSTA}/`}
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
        </div>
        <p className="kfoot-tag"><IcHeart className="ci" /> {t.tagline}</p>
        <p className="kfoot-copy">{t.foot_copy}</p>
      </footer>
    </div>
  );
}
