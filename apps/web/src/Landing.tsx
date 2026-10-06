import { Fragment, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent as RKeyboardEvent, type MouseEvent as RMouseEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { accountGateHref } from "./Auth";
import logo from "./assets/logo.png";
import "./landing.css";
import "./landing-flip-fold.css";

export type Lang = "pt" | "en" | "es";

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
/** Hero strip: capa, página aberta, criança lendo. */
const HERO_STRIP: { name: string; cover: HeroAsset; page: HeroAsset; photo: HeroAsset }[] = [
  {
    name: "Meu Pai, Meu Herói",
    cover: heroAsset("capa-meupai-heroi.png"),
    page: heroAsset("pagina-meupai-heroi.png"),
    photo: heroAsset("foto-meupai-heroi.png"),
  },
  {
    name: "Nano",
    cover: heroAsset("capa-nanoaventuras.jpg", "capa-nanoaventuras-en.jpg", "capa-nanoaventuras-es.jpg"),
    page: heroAsset("pagina-nanoaventuras.jpg", "pagina-nanoaventuras-en.jpg", "pagina-nanoaventuras-es.jpg"),
    photo: heroAsset("foto-nanoaventuras.jpg", "foto-nanoaventuras-en.jpg", "foto-nanoaventuras-es.jpg"),
  },
  {
    name: "Amor de Bisavó",
    cover: heroAsset("capa-amordebisavo.jpg", "capa-amordebisavo-en.jpg", "capa-amordebisavo-es.jpg"),
    page: heroAsset("pagina-amordebisavo.jpg", "pagina-amordebisavo-en.jpg", "pagina-amordebisavo-es.jpg"),
    photo: heroAsset("foto-amordebisavo.jpg", "foto-amordebisavo-en.jpg", "foto-amordebisavo-es.jpg"),
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
    name: "Facundo",
    cover: heroAsset("capa-facundo-motocross.jpg"),
    page: heroAsset("pagina-facundo-motocross.jpg"),
    photo: heroAsset("foto-facundo-motocross.jpg"),
  },
  {
    name: "Amor de Tia",
    cover: heroAsset("capa-amordetia.png"),
    page: heroAsset("pagina-amordetia.png"),
    photo: heroAsset("foto-amordetia.png"),
  },
  {
    name: "Davi, o Menino Pastor",
    cover: heroAsset("capa-davi-pastor.png"),
    page: heroAsset("pagina-davi-pastor.png"),
    photo: heroAsset("foto-davi-pastor.png"),
  },
  {
    name: "Enzo, Meu Primo Predileto",
    cover: heroAsset("capa-enzo-primo.png"),
    page: heroAsset("pagina-enzo-primo.png"),
    photo: heroAsset("foto-enzo-primo.png"),
  },
  {
    name: "Lucas e seu amigo Max",
    cover: heroAsset("capa-lucas-max.png"),
    page: heroAsset("pagina-lucas-max.png"),
    photo: heroAsset("foto-lucas-max.png"),
  },
  {
    name: "Esther e os Superpoderes da Higiene",
    cover: heroAsset("capa-esther-higiene.png"),
    page: heroAsset("pagina-esther-higiene.png"),
    photo: heroAsset("foto-esther-higiene.png"),
  },
  {
    name: "Meme e Tata",
    cover: heroAsset("capa-natalmemetata.jpg", "capa-natalmemetata-en.jpg", "capa-natalmemetata-es.jpg"),
    page: heroAsset("pagina-natalmemetata.jpg", "pagina-natalmemetata-en.jpg", "pagina-natalmemetata-es.jpg"),
    photo: heroAsset("foto-natalmemetata.jpg", "foto-natalmemetata-en.jpg", "foto-natalmemetata-es.jpg"),
  },
];
/** Livros da /cartoon que têm capa, página ou foto em desenho. Os demais ficam só na principal. */
const CARTOON_HERO: Record<string, { cover?: string; page?: string; photo?: string }> = {
  "Amor de Bisavó": { cover: "cartoon-capa-bisavo.jpg", page: "cartoon-pagina-bisavo.jpg", photo: "cartoon-foto-bisavo.jpg" },
  "Amor de Mãe": { cover: "cartoon-capa-amordemae.jpg", page: "cartoon-pagina-amordemae.jpg", photo: "cartoon-foto-amordemae.jpg" },
  "Davi, o Menino Pastor": { cover: "cartoon-capa-davi.jpg", page: "cartoon-pagina-davi.jpg", photo: "cartoon-foto-davi.jpg" },
  "Enzo, Meu Primo Predileto": { cover: "cartoon-capa-enzo.jpg", page: "cartoon-pagina-enzo.jpg", photo: "cartoon-foto-enzo.jpg" },
};
const CARTOON_COVER: Record<number, string | Record<Lang, string>> = {
  5: "cartoon-capa-nicolas.jpg",
  6: "cartoon-capa-amordemae.jpg",
  7: "cartoon-capa-matteo.jpg",
  8: "cartoon-capa-bisavo.jpg",
  11: "cartoon-capa-maya.jpg",
  12: "cartoon-capa-mako.png",
  19: "cartoon-capa-amordetia.png",
  20: "cartoon-capa-davi.png",
  22: "cartoon-capa-enzo.jpg",
  23: "cartoon-capa-lucas.png",
  30: { pt: "cartoon-capa-avo.png", en: "cartoon-capa-avo-en.png", es: "cartoon-capa-avo-en.png" },
};
/** Faixa do /cartoon: cenas diferentes lado a lado, não só família lendo no sofá. */
const CARTOON_REVIEW_PHOTOS = [
  { tab: "cartoon-foto-nicolas.jpg", name: "Nicolas" },
  { tab: "cartoon-foto-davi.jpg", name: "Davi" },
  { tab: "cartoon-foto-maya.jpg", name: "Maya" },
  { tab: "cartoon-foto-enzo.jpg", name: "Enzo" },
  { tab: "cartoon-foto-amordemae.jpg", name: "Amor de Mãe" },
  { tab: "cartoon-foto-natal.jpg", name: "Meme e Tata" },
  { tab: "cartoon-foto-matteo.jpg", name: "Matteo" },
  { tab: "cartoon-foto-bisavo.jpg", name: "Amor de Bisavó" },
] as const;

/* ------- exemplos reais em apps/web/public/exemplos/ ------- */
const HOW_IMGS = ["dica-boa.png", "personagem-avatar.jpg", "cena-dino-floresta.jpg"];
const HOW_SCENE_IMGS = ["como-envia.jpg", "como-cria.jpg", "como-recebe.jpg"];
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
function catalogCoverFile(i: number, lang: Lang, variant: "photo" | "cartoon"): string {
  const cartoon = CARTOON_COVER[i];
  if (variant === "cartoon" && cartoon) return catalogImgSrc(cartoon, lang);
  return catalogImgSrc(CATALOG_IMGS[i], lang);
}
const CATALOG_IMGS: CatalogImg[] = [
  "capa-martin-goleiro.jpg",
  "capa-emilia-bailarina.jpg",
  "capa-antonio-bicicleta.jpg",
  "capa-sofia-alfabeto.png",
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
  { pt: "capa-amordetia.png", en: "capa-amordetia.png", es: "capa-amordetia.png" },
  { pt: "capa-davi-pastor.png", en: "capa-davi-pastor.png", es: "capa-davi-pastor.png" },
  { pt: "capa-meupai-heroi.png", en: "capa-meupai-heroi.png", es: "capa-meupai-heroi.png" },
  { pt: "capa-enzo-primo.png", en: "capa-enzo-primo.png", es: "capa-enzo-primo.png" },
  { pt: "capa-lucas-max.png", en: "capa-lucas-max.png", es: "capa-lucas-max.png" },
  { pt: "capa-esther-higiene.png", en: "capa-esther-higiene.png", es: "capa-esther-higiene.png" },
  "capa-construtor.png",
  { pt: "capa-heroi-bombeiro.png", en: "capa-heroi-bombeiro-en.png", es: "capa-heroi-bombeiro-es.png" },
  { pt: "capa-heroi-policia.png", en: "capa-heroi-policia-en.png", es: "capa-heroi-policia-es.png" },
  { pt: "capa-heroi-aranha.png", en: "capa-heroi-aranha-en.png", es: "capa-heroi-aranha-es.png" },
  { pt: "capa-tia-especial.png", en: "capa-tia-especial-en.png", es: "capa-tia-especial-es.png" },
  { pt: "cartoon-capa-avo.png", en: "cartoon-capa-avo-en.png", es: "cartoon-capa-avo-en.png" },
];
const CATALOG_THEMES = [
  "adventure",
  "princess",
  "adventure",
  "alfabetizacao_inicial",
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
  "family_love",
  "biblico",
  "fathers_day",
  "family_love",
  "pets",
  "higiene_desfralde",
  "adventure",
  "superhero",
  "superhero",
  "pets",
  "family_love",
  "grandparents_love",
];
/** Janela da vitrine. Era 15; desceu 1 quando o Bruno saiu do meio da lista. */
const CATALOG_LIMIT = 14;
/** Índices fora do catálogo realista: capas em desenho e o aniversário da Ester. */
const CATALOG_CARTOON_INDEXES = new Set([0, 1, 2, 3, 4, 13, 30]);
/** Livros novos em português, depois do limite dos 15 primeiros. */
const CATALOG_NEW_INDEXES = new Set([19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]);
/** Primeiros da vitrine: livros novos, depois Meu Pai, Davi e Enzo. */
const CATALOG_LEAD = [25, 26, 27, 28, 29, 30, 21, 20, 22];
type CatalogCoverChoice = "soft" | "hard";
type CatalogSizeChoice = "M" | "P";
function catalogCoverChoice(cover?: string): CatalogCoverChoice {
  return cover === "Hard" ? "hard" : "soft";
}
function catalogSizeChoice(size?: string): CatalogSizeChoice {
  return size === "P" ? "P" : "M";
}
const VIDEO_IMGS = ["mar-2.jpg", "flor-2.jpg", "dino-2.jpg"];
const VIDEO_SRCS: (string | null)[] = ["video-mar.mp4", "video-flor.mp4", "video-dino.mp4"];
const FEELING_THEMES = new Set(["literacia_emocional", "rotina_dormir", "compartilhar_revezar", "consciencia_corporal"]);
const CATALOG_SECTION_THEMES: Record<string, readonly string[]> = {
  aventuras: ["adventure", "princess", "sport", "dinosaurs", "underwater", "space", "superhero"],
  "voce-e-eu": ["mothers_day", "fathers_day", "grandparents_love", "family_love", "recem_nascidos", "casamento", "pets"],
  ocasioes: ["christmas", "birthday"],
  educativo: ["animais_sons", "higiene_desfralde", "biblico"],
};
const NAV_CAT_META = [
  {
    id: "aventuras",
    color: "#7aa2ff",
    subs: [
      { href: "/app?tema=adventure" },
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
      { href: "/app?tema=sport", catalogI: 4 },
      { href: "/app?tema=adventure", catalogI: 10 },
    ],
  },
  {
    id: "voce-e-eu",
    color: "#b48ad4",
    subs: [
      { href: "/app?tema=mothers_day" },
      { href: "/app?tema=fathers_day" },
      { href: "/app?tema=grandparents_love" },
      { href: "/app?tema=family_love" },
      { href: "/app" },
      { href: "/app?tema=recem_nascidos" },
      { href: "/app?tema=casamento" },
      { href: "/app?tema=pets" },
    ],
    feats: [
      { href: "/app?tema=mothers_day", catalogI: 5 },
      { href: "/app?tema=grandparents_love", catalogI: 8 },
      { href: "/app?tema=family_love", catalogI: 7 },
      { href: "/app?tema=mothers_day", catalogI: 6 },
    ],
  },
  {
    id: "ocasioes",
    color: "#f0b429",
    subs: [
      { href: "/app?tema=dia_da_mulher", when: { month: 3, day: 8 } },
      { href: "/app?tema=dia_da_sogra", when: { month: 3, day: 26 } },
      { href: "/app?tema=easter", when: "easter" },
      { href: "/app?tema=mothers_day", when: { month: 5, day: 10 } },
      { href: "/app?tema=dia_da_familia", when: { month: 5, day: 15 } },
      { href: "/app?tema=dia_do_irmao", when: { month: 5, day: 30 } },
      { href: "/app?tema=dia_dos_namorados", when: { month: 6, day: 12 } },
      { href: "/app?tema=dia_do_amigo", when: { month: 7, day: 20 } },
      { href: "/app?tema=grandparents_love", when: { month: 7, day: 26 } },
      { href: "/app?tema=tio_tia", when: { month: 7, day: 26 } },
      { href: "/app?tema=fathers_day", when: { month: 8, day: 9 } },
      { href: "/app?tema=dia_dos_filhos", when: { month: 8, day: 11 } },
      { href: "/app?tema=independencia", when: { month: 9, day: 7 } },
      { href: "/app?tema=dia_do_idoso", when: { month: 10, day: 1 } },
      { href: "/app?tema=pets", when: { month: 10, day: 4 } },
      { href: "/app?tema=childrens_day", when: { month: 10, day: 12 } },
      { href: "/app?tema=christmas", when: { month: 12, day: 25 } },
      { href: "/app?tema=birthday" },
    ],
    feats: [
      { href: "/app?tema=christmas", catalogI: 9 },
      { href: "/app?tema=mothers_day", catalogI: 5 },
      { href: "/app?tema=grandparents_love", catalogI: 8 },
      { href: "/app?tema=fathers_day", catalogI: 21 },
    ],
  },
  {
    id: "educativo",
    color: "#5ec4a8",
    subs: [
      { href: "/app?tema=biblico" },
      { href: "/app?tema=cores" },
      { href: "/app?tema=higiene_desfralde" },
      { href: "/app?tema=animais_sons" },
      { href: "/app?tema=literacia_emocional" },
      { href: "/app?tema=rotina_dormir" },
      { href: "/app?tema=compartilhar_revezar" },
      { href: "/app?tema=consciencia_corporal" },
    ],
    feats: [
      { href: "/app?tema=animais_sons", catalogI: 23 },
      { href: "/app?tema=higiene_desfralde", catalogI: 24 },
      { href: "/app?tema=biblico", catalogI: 20 },
    ],
  },
] as const;
/** Livros reais de cada tema do menu. O painel troca esta lista ao passar o mouse no subtema. */
const MENU_BOOKS: Record<string, readonly number[]> = {
  adventure: [2, 10, 25],
  dinosaurs: [18],
  underwater: [17],
  space: [16],
  princess: [1],
  superhero: [15, 26, 27],
  sport: [0, 4],
  mothers_day: [5, 6],
  fathers_day: [21, 14],
  grandparents_love: [8],
  dia_do_idoso: [8, 30],
  family_love: [7, 29],
  pets: [11, 12, 23, 28],
  dia_da_mulher: [6, 5, 8, 19],
  dia_da_familia: [7, 19, 21, 22],
  tio_tia: [19, 29],
  christmas: [9],
  animais_sons: [23],
  higiene_desfralde: [24],
  biblico: [20],
};
function themeFromHref(href: string): string | null {
  // Links podem ser /app?tema=… ou /cadastro?next=%2Fapp%3Ftema%3D…
  let target = href;
  try {
    const next = new URL(href, "https://storyrus.local").searchParams.get("next");
    if (next && next.startsWith("/")) target = next;
  } catch {
    /* ignore */
  }
  const match = target.match(/[?&]tema=([^&]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}
type OccasionWhen = { month: number; day: number } | "easter";
function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}
function easterSunday(year: number): Date {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(year, month - 1, day);
}
export function nextOccasionDate(when: OccasionWhen, today: Date): Date {
  const start = startOfDay(today);
  if (when === "easter") {
    const thisYear = easterSunday(start.getFullYear());
    return thisYear >= start ? thisYear : easterSunday(start.getFullYear() + 1);
  }
  const next = new Date(start.getFullYear(), when.month - 1, when.day);
  return next >= start ? next : new Date(start.getFullYear() + 1, when.month - 1, when.day);
}
function shiftMonths(date: Date, months: number): Date {
  const next = new Date(date);
  next.setMonth(next.getMonth() + months);
  return next;
}
/** A data entra no menu quando cai entre 6 meses atrás e 4 meses à frente. */
export function occasionDue(when: OccasionWhen, today: Date): boolean {
  const start = startOfDay(today);
  const past = shiftMonths(start, -6);
  const future = shiftMonths(start, 4);
  const year = start.getFullYear();
  const dates = when === "easter"
    ? [year - 1, year, year + 1].map(easterSunday)
    : [year - 1, year, year + 1].map((y) => new Date(y, when.month - 1, when.day));
  return dates.some((date) => date >= past && date <= future);
}
function SubLabel({ label }: { label: string }) {
  const [name, date] = label.split(" · ");
  if (!date) return label;
  return (
    <>
      <span className="kcat-sub-name">{name}</span>
      <span className="kcat-sub-date">{date}</span>
    </>
  );
}
/** Nome da criança no exemplo, para o estúdio trocar pelo nome que a família digitar. */
const HERO_BY_CATALOG: Record<number, string> = {
  0: "Martin",
  1: "Emilia",
  2: "Antonio",
  3: "Sofia",
  4: "Cristobal",
  5: "Nicolas",
  7: "Matteo",
  10: "Nano",
  11: "Maya",
  12: "Mako",
  23: "Lucas",
  13: "Ester",
  14: "Raquel",
  15: "Rebeca",
  16: "Abigail",
  17: "Miriam",
  18: "Noé",
  20: "Davi",
};
function personalizeHref(opts: {
  theme: string;
  title: string;
  historia?: string;
  heroi?: string;
  size: "M" | "P";
  cover: "soft" | "hard";
  modo: "realista" | "cartoon";
  catalogI?: number;
}) {
  const q = new URLSearchParams();
  q.set("tema", opts.theme);
  q.set("campos", "nome");
  q.set("titulo", opts.title);
  if (opts.historia) q.set("historia", opts.historia);
  if (opts.heroi) q.set("heroi", opts.heroi);
  q.set("tamanho", opts.size);
  q.set("capa", opts.cover);
  q.set("modo", opts.modo);
  return accountGateHref(`/app?${q.toString()}`);
}
function studioHref(opts: {
  tema: string;
  titulo?: string;
  historia?: string;
  heroi?: string;
  size?: "M" | "P";
  cover?: "soft" | "hard";
  modo?: "realista" | "cartoon";
  catalogI?: number;
}) {
  const q = new URLSearchParams();
  q.set("tema", opts.tema);
  q.set("campos", "nome");
  if (opts.titulo) q.set("titulo", opts.titulo);
  if (opts.historia) q.set("historia", opts.historia);
  if (opts.heroi) q.set("heroi", opts.heroi);
  q.set("tamanho", opts.size ?? "M");
  q.set("capa", opts.cover ?? "hard");
  q.set("modo", opts.modo ?? "realista");
  return accountGateHref(`/app?${q.toString()}`);
}
const exUrl = (f: string) => (f.startsWith("http://") || f.startsWith("https://") ? f : `${import.meta.env.BASE_URL}exemplos/${f}`);

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
    nav: ["Como Funciona", "Livros", "Vídeos", "FAQ"],
    reviews_link: "Avaliações",
    videos_link: "Vídeos",
    my_books: "Meus Livros",
    see_all_books: "Ver todos os livros",
    view_all: "Ver todos",
    cat_empty: "Ainda não temos um exemplo neste tema.",
    cats_label: "Livros",
    realistic_link: "Realista",
    cartoon_link: "Livros Cartoon",
    quick_links: "Acessos Rápidos",
    font_label: "Fonte do título",
    explore: "Explorar agora",
    eyebrow: "Eternize momentos. Presenteie familiares com uma história inesquecível.",
    h_pre: "Transforme uma foto em uma ", w1: "história inesquecível", c1: ", onde seu filho é o ", w2: "protagonista", h_suf: " !",
    lead: "Você envia a foto e nós transformamos seu filho em um personagem ilustrado, criando uma aventura personalizada especialmente para ele — um livro para presentear a família e guardar para sempre.",
    cta_login: "Entrar",
    cta_play: "Criar conta",
    hero_cta: "Criar meu livro",
    cta_story: "Criar minha história",
    hero_sign: "Uma foto. Uma história. Uma memória eterna.",
    book_carousel: "Carrossel de livros",
    cats: [
      {
        name: "Aventuras",
        subs: ["Aventura", "Dinossauros", "Fundo do Mar", "Espaço", "Princesas", "Super-heróis", "Esportes"],
        feats: ["Princesas", "Aventura", "Cristobal e seu Esporte Favorito", "Nano e suas Aventuras"],
      },
      {
        name: "Você e Eu",
        subs: ["Mamãe e Eu", "Papai e Eu", "Vovó e Eu", "Nossa Família", "Irmãos e Primos", "Recém-nascidos", "Casamento", "Pets"],
        feats: ["Mamãe e Eu", "Vovó e Eu", "Nossa Família", "O Amor de Mãe"],
      },
      {
        name: "Ocasiões Especiais",
        subs: [
          "Dia Internacional da Mulher · 8 de março",
          "Dia da Sogra · 26 de março",
          "Páscoa",
          "Dia das Mães · 10 de maio",
          "Dia Internacional da Família · 15 de maio",
          "Dia do Irmão · 30 de maio",
          "Dia dos Namorados · 12 de junho",
          "Dia do Amigo · 20 de julho",
          "Dia dos Avós · 26 de julho",
          "Dia do Tio e da Tia · 26 de julho",
          "Dia dos Pais · 9 de agosto",
          "Dia dos Filhos · 11 de agosto",
          "Independência do Brasil · 7 de setembro",
          "Dia Internacional do Idoso · 1 de outubro",
          "Dia dos Animais · 4 de outubro",
          "Dia das Crianças · 12 de outubro",
          "Natal · 25 de dezembro",
          "Aniversário",
        ],
        feats: ["Natal", "Dia das Mães", "Dia dos Avós", "Dia dos Pais"],
      },
      {
        name: "Educativo",
        subs: ["Bíblico", "Cores", "Higiene", "Animais", "Sentimentos", "Hora de Dormir", "Compartilhar", "Corpo"],
        feats: ["Animais", "Higiene", "Davi, o Menino Pastor"],
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
    hiw_title: "Como Funciona", hiw_sub: "Você manda as fotos. A gente faz o livro, com seu filho como personagem.",
    hiw: [
      { t: "Envie as fotos", p: "Da criança e de quem entra na história." },
      { t: "A gente cria o livro", p: "Um personagem parecido com a foto e uma história só de vocês." },
      { t: "O livro fica pronto", p: "Páginas ilustradas para ler e guardar." },
    ],
    hiw_main: [
      { t: "Envie foto do protagonista (original)", p: "Envie fotos nítidas do personagem, protagonista da sua história." },
      { t: "Envie fotos do personagem adicional", p: "Adicione fotos de um ou mais personagens relacionadas à história que deseja criar." },
      { t: "Revise e aprove (livro capa)", p: "Revise a prévia, capa e páginas para aprovação. Após sua confirmação, o livro é enviado para produção." },
    ],
    hiw_foot: [
      { t: "Envie a Foto e Defina os Detalhes", p: "Escolha o tema e o formato do livro." },
      { t: "Criamos o Personagem e a História", p: "História, capa e páginas com o mesmo rosto da criança." },
      { t: "Você Recebe e Aprova o Livro", p: "Veja a prévia, aprove e receba o livro impresso." },
    ],
    shot_sub: "Envie a foto e defina os detalhes.",
    shots: [
      { t: "A criança", p: "3 a 5 fotos de frente, bem iluminadas, com o rosto inteiro. Sem filtro, chapéu ou óculos." },
      { t: "Família e pets", p: "2 ou 3 fotos de cada pessoa, sozinha. Do pet, uma de frente e outra de corpo inteiro." },
      { t: "Dados do livro", p: "Nome, idade, tema e idioma: português, espanhol ou inglês." },
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
    vid_title: "Vídeos Narrados", vid_sub: "A mesma história ganha voz, trilha e movimento — perfeita para assistir em família.",
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
    cat_title: "Nossos Livros", cat_sub: "Cada tema se transforma em uma história ilustrada, com seu filho como protagonista da própria história.",
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
      { t: "Miriam e os Segredos do Fundo do Mar", p: "Tartarugas, corais e amizade: o seu filho explora o oceano com cuidado e encanto.", cover: "Hard", size: "M", tag: "Fundo do Mar", quote: "Cuidar do mar é cuidar dos amigos." },
      { t: "Noé na Terra dos Dinossauros", p: "Fósseis, amigos gigantes e coragem: uma expedição pré-histórica com o seu filho.", cover: "Hard", size: "M", tag: "Dinossauros", quote: "Descobrir juntos é a melhor aventura." },
      { t: "Amor de Tia", p: "O carinho da tia em cada página: colo, riso e um amor que a família guarda para sempre.", cover: "Hard", size: "M", tag: "Amor de tia", quote: "Tia é abraço que não acaba." },
      { t: "Davi, o Menino Pastor", p: "Um menino, sua harpa e as ovelhas: coragem e fé numa história para guardar para sempre.", cover: "Hard", size: "M", tag: "Fé e coragem", quote: "Pequeno no campo, grande no coração." },
      { t: "Meu Pai, Meu Herói", p: "Papai e o bebê, lado a lado: proteção, carinho e um herói só da família.", cover: "Hard", size: "M", tag: "Papai herói", quote: "Meu herói tem o colo do papai." },
      { t: "Enzo, Meu Primo Predileto", p: "Dois primos, um abraço e o mar: amizade que a família nos dá, para guardar para sempre.", cover: "Hard", size: "M", tag: "Amor de primo", quote: "Primo é amigo que a família nos dá." },
      { t: "Lucas e seu amigo Max", p: "Um menino e seu cachorro: cuidado, passeio e uma amizade para guardar para sempre.", cover: "Hard", size: "M", tag: "Amigo fiel", quote: "Max é o amigo de todas as horas." },
      { t: "Esther e os Superpoderes da Higiene", p: "Mãos limpas, dentes escovados e um sorriso: hábitos de higiene que viram superpoderes.", cover: "Hard", size: "M", tag: "Higiene", quote: "Cuidar de si é um superpoder." },
      { t: "Pequeno Construtor, Grande Empreendedor", p: "Capacete, blocos e um plano no papel: construir, tentar de novo e ver a ideia ficar de pé.", cover: "Hard", size: "M", tag: "Construir e criar", quote: "Pequenas mãos, grandes ideias." },
      { t: "Meu Herói Favorito, o Bombeiro", p: "Sirene, coragem e um herói de verdade: o bombeiro que cuida da cidade e da família.", cover: "Hard", size: "M", tag: "Heróis de verdade", quote: "Meu herói protege todo mundo." },
      { t: "Meu Herói Favorito, o Policial", p: "Farda, cuidado e um herói da cidade: o policial que protege quem a gente ama.", cover: "Hard", size: "M", tag: "Heróis de verdade", quote: "Meu herói cuida da gente todos os dias." },
      { t: "Meu Herói Favorito, a Aranha", p: "Uma teia no jardim e uma amizade miúda: descobrir a natureza com cuidado e encanto.", cover: "Hard", size: "M", tag: "Natureza e amizade", quote: "Até o menor amigo pode ser um herói." },
      { t: "Tia Especial, Não Existe Igual", p: "Passeio, colo e risada: a tia que transforma qualquer dia numa memória para guardar.", cover: "Hard", size: "M", tag: "Amor de tia", quote: "Com a tia, todo dia vira passeio." },
      { t: "Amor de Avô, Meu Porto Seguro", p: "O colo do avô, o lago e um abraço que não acaba: um porto seguro só da família.", cover: "Hard", size: "M", tag: "Amor de avô", quote: "No colo do avô, encontro meu porto seguro." },
    ],
    promise_title: "Um Presente Personalizado para Eternizar Momentos Inesquecíveis.",
    promise_sub: "Da foto à prévia final, cada detalhe é criado com carinho, dando vida a um presente único para toda a vida.",
    promise: [
      { t: "Privacidade da Foto", p: "A foto que você envia é usada só para criar o livro — nunca para divulgação. Os exemplos desta página são demonstrações da plataforma." },
      { t: "Impressão Pensada como Presente", p: "Preparado para ficar lindo em mãos, na leitura em família e na hora de entregar." },
      { t: "Prévia antes de Avançar", p: "Você vê a capa e as páginas e entende o que está criando antes de finalizar." },
      { t: "Entrega sem Complicação", p: "O PDF fica pronto na plataforma. O livro impresso é sob consulta — em até 24h enviamos a cotação e o prazo." },
    ],
    faq_title: "Perguntas Frequentes", faq_sub: "Tudo o que você precisa saber.",
    faq: [
      { q: "Como crio um livro personalizado?", a: "Escolha um tema, envie uma foto da criança e adicione o nome e uma dedicatória. A IA transforma a foto em ilustrações e você vê a prévia antes de finalizar." },
      { q: "Posso ver o livro antes?", a: "Sim! Você recebe uma prévia completa (capa e páginas) antes de baixar ou pedir a impressão." },
      { q: "A foto e os dados da criança estão seguros?", a: "Sim. Usamos a foto que você envia apenas para criar o livro e não compartilhamos seus dados. Os exemplos da página inicial são demonstrações, separados do que você envia." },
      { q: "Recebo digital ou impresso?", a: "O e-book digital fica pronto na plataforma. Se quiser o impresso, peça a cotação depois de aprovar o livro." },
      { q: "Posso pedir alterações?", a: "Pode! Ajuste o nome, a dedicatória e regenere as ilustrações na prévia até ficar do seu jeito." },
      { q: "Como funciona o vídeo narrado?", a: "Depois do ebook pronto, na tela de resultado você pode gerar o vídeo narrado (voz + cenas ilustradas) ou uma animação curta do personagem." },
    ],
    rev_title: "O que as Famílias Dizem", rev_sub: "Histórias que viraram memórias para sempre.",
    reviews: [
      { q: "Meu filho pede para ler o livro dele toda noite. Emocionante vê-lo como herói!", name: "Ana C." },
      { q: "Enviei uma foto e recebi um livro lindo. Virou o presente de aniversário da vovó.", name: "Rafael M." },
      { q: "A ilustração ficou idêntica ao meu bebê. Vamos guardar para sempre.", name: "Juliana P." },
      { q: "O vídeo narrado fez a família toda se emocionar. Vale cada segundo.", name: "Marcos e Bia" },
    ],
    features: ["Histórias personalizadas", "Conexão em família", "Memórias que ficam para sempre", "Um presente inesquecível"],
    band_title: "Pronto para Virar Protagonista?",
    band_sub: "Envie sua foto e receba uma história única, criada só para você.",
    band_cta: "Criar minha conta",
    tagline: "Feito com amor. Criado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  en: {
    nav: ["How It Works", "Books", "Videos", "FAQ"],
    reviews_link: "Reviews",
    videos_link: "Videos",
    my_books: "My Books",
    see_all_books: "See all books",
    view_all: "View all",
    cat_empty: "We don't have an example for this theme yet.",
    cats_label: "Books",
    realistic_link: "Realistic",
    cartoon_link: "Cartoon Books",
    quick_links: "Quick Links",
    font_label: "Cover font",
    explore: "Explore now",
    eyebrow: "Preserve moments. Gift your family an unforgettable story.",
    h_pre: "Turn a photo into an ", w1: "unforgettable story", c1: ", where your child is the ", w2: "hero", h_suf: " !",
    lead: "You send the photo and we turn your child into an illustrated character, creating an adventure made just for them — a book to gift the family and keep forever.",
    cta_login: "Log in",
    cta_play: "Sign up",
    hero_cta: "Create my book",
    cta_story: "Create my story",
    hero_sign: "One photo. One story. One lasting memory.",
    book_carousel: "Book carousel",
    cats: [
      {
        name: "Adventures",
        subs: ["Adventure", "Dinosaurs", "Under the Sea", "Space", "Princesses", "Superheroes", "Sports"],
        feats: ["Princesses", "Adventure", "Cristobal and His Favorite Sport", "Nano and His Adventures"],
      },
      {
        name: "You and Me",
        subs: ["Mommy and Me", "Daddy and Me", "Grandma and Me", "Our Family", "Siblings and Cousins", "Newborns", "Wedding", "Pets"],
        feats: ["Mommy and Me", "Grandma and Me", "Our Family", "A Mother's Love"],
      },
      {
        name: "Special Occasions",
        subs: [
          "International Women's Day · March 8",
          "Mother-in-law's Day · March 26",
          "Easter",
          "Mother's Day · May 10",
          "International Family Day · May 15",
          "Siblings' Day · May 30",
          "Valentine's Day · June 12",
          "Friendship Day · July 20",
          "Grandparents' Day · July 26",
          "Aunt and Uncle's Day · July 26",
          "Father's Day · August 9",
          "Sons and Daughters Day · August 11",
          "Brazil's Independence Day · September 7",
          "International Day of Older Persons · October 1",
          "World Animal Day · October 4",
          "Children's Day · October 12",
          "Christmas · December 25",
          "Birthday",
        ],
        feats: ["Christmas", "Mother's Day", "Grandparents' Day", "Father's Day"],
      },
      {
        name: "Educational",
        subs: ["Biblical", "Colors", "Hygiene", "Animals", "Feelings", "Bedtime", "Sharing", "Body"],
        feats: ["Animals", "Hygiene", "David, the Shepherd Boy"],
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
    hiw_title: "How It Works", hiw_sub: "You send the photos. We make the book, with your child as the character.",
    hiw: [
      { t: "Send the photos", p: "Of your child and anyone else in the story." },
      { t: "We make the book", p: "A character that looks like the photo, and a story just for you." },
      { t: "The book is ready", p: "Illustrated pages to read and keep." },
    ],
    hiw_main: [
      { t: "Send the protagonist photo (original)", p: "Send clear photos of the character, the protagonist of your story." },
      { t: "Send additional character photos", p: "Add photos of one or more characters related to the story you want to create." },
      { t: "Review and approve (book cover)", p: "Review the preview, cover, and pages for approval. After you confirm, the book goes to production." },
    ],
    hiw_foot: [
      { t: "Send the Photo and Set the Details", p: "Choose the theme and the book format." },
      { t: "We Create the Character and the Story", p: "Story, cover, and pages with the same face as the child." },
      { t: "You Receive and Approve the Book", p: "See the preview, approve it, and receive the printed book." },
    ],
    shot_sub: "Send the photo and set the details.",
    shots: [
      { t: "The child", p: "3 to 5 front-facing, well-lit photos, with the full face. No filter, hat, or sunglasses." },
      { t: "Family and pets", p: "2 or 3 photos of each person, alone. For a pet, one facing forward and one full body." },
      { t: "Book details", p: "Name, age, theme, and language: Portuguese, Spanish, or English." },
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
    vid_title: "Narrated Videos", vid_sub: "The same story gains voice, music and motion — perfect to watch together.",
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
    cat_title: "Our Books", cat_sub: "Each theme becomes an illustrated story, with your child as the hero of their own story.",
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
      { t: "Miriam and the Secrets of the Deep Sea", p: "Turtles, coral and friendship: your child explores the ocean with care and wonder.", cover: "Hard", size: "M", tag: "Under the Sea", quote: "Caring for the sea is caring for friends." },
      { t: "Noé in the Land of Dinosaurs", p: "Fossils, giant friends and courage: a prehistoric expedition with your child.", cover: "Hard", size: "M", tag: "Dinosaurs", quote: "Discovering together is the best adventure." },
      { t: "An Aunt's Love", p: "An aunt's tenderness on every page: a hug, a laugh, and a love the family keeps forever.", cover: "Hard", size: "M", tag: "Aunt's love", quote: "An aunt's hug never ends." },
      { t: "David, the Shepherd Boy", p: "A boy, his harp and the sheep: courage and faith in a story to keep forever.", cover: "Hard", size: "M", tag: "Faith and courage", quote: "Small in the field, great in heart." },
      { t: "My Dad, My Hero", p: "Dad and baby, side by side: protection, care, and a hero who belongs to the family.", cover: "Hard", size: "M", tag: "Dad the hero", quote: "My hero has Dad's arms." },
      { t: "Enzo, My Favorite Cousin", p: "Two cousins, one hug and the sea: a friendship the family gives, to keep forever.", cover: "Hard", size: "M", tag: "Cousin love", quote: "A cousin is the friend family gives us." },
      { t: "Lucas and his friend Max", p: "A boy and his dog: care, walks and a friendship to keep forever.", cover: "Hard", size: "M", tag: "Loyal friend", quote: "Max is a friend for every hour." },
      { t: "Esther and the Superpowers of Hygiene", p: "Clean hands, brushed teeth and a smile: hygiene habits that become superpowers.", cover: "Hard", size: "M", tag: "Hygiene", quote: "Taking care of yourself is a superpower." },
      { t: "Little Builder, Big Entrepreneur", p: "A hard hat, blocks and a plan on paper: build, try again and watch the idea stand up.", cover: "Hard", size: "M", tag: "Build and create", quote: "Small hands, big ideas." },
      { t: "My Favorite Hero, the Firefighter", p: "A siren, courage and a real hero: the firefighter who looks after the city and the family.", cover: "Hard", size: "M", tag: "Real heroes", quote: "My hero protects everyone." },
      { t: "My Favorite Hero, the Police Officer", p: "A uniform, care and a hero of the city: the officer who protects the people we love.", cover: "Hard", size: "M", tag: "Real heroes", quote: "My hero looks after us every day." },
      { t: "My Favorite Hero, the Spider", p: "A web in the garden and a tiny friendship: discovering nature with care and wonder.", cover: "Hard", size: "M", tag: "Nature and friendship", quote: "Even the smallest friend can be a hero." },
      { t: "A Special Aunt, One of a Kind", p: "A walk, a hug and a laugh: the aunt who turns any day into a memory to keep.", cover: "Hard", size: "M", tag: "Aunt's love", quote: "With aunt, every day becomes an outing." },
      { t: "Grandpa's Love, My Safe Harbor", p: "Grandpa's arms, the lake and a hug that never ends: a safe harbor just for the family.", cover: "Hard", size: "M", tag: "Grandpa's love", quote: "In grandpa's arms, I find my safe harbor." },
    ],
    promise_title: "Every Detail Crafted to Feel Special",
    promise_sub: "From the photo to the preview, everything is made so the book is ready to gift.",
    promise: [
      { t: "Photo Privacy", p: "The photo you upload is used only to create the book — never for promotion. The examples on this page are platform demos." },
      { t: "Print Made as a Gift", p: "Prepared to look beautiful in hand, in shared reading and at the moment you give it." },
      { t: "Preview Before You Continue", p: "You see the cover and pages and understand what you're creating before finishing." },
      { t: "Hassle-Free Delivery", p: "The PDF is ready on the platform. Printed books are quoted on request — we send price and timing within 24 hours." },
    ],
    faq_title: "Frequently Asked Questions", faq_sub: "Everything you need to know.",
    faq: [
      { q: "How do I create a personalized book?", a: "Pick a theme, upload a photo of your child and add the name and a dedication. The AI turns the photo into illustrations and you see a preview before finishing." },
      { q: "Can I see the book before?", a: "Yes! You get a full preview (cover and pages) before downloading or ordering the print." },
      { q: "Are my child's photo and data safe?", a: "Yes. We use the photo you upload only to create the book and never share your data. Homepage examples are demos, separate from what you send." },
      { q: "Digital or printed?", a: "The digital e-book is ready on the platform. If you want a printed copy, request a quote after you approve the book." },
      { q: "Can I request changes?", a: "You can! Adjust the name, the dedication and regenerate the illustrations in the preview." },
      { q: "How does the narrated video work?", a: "After the ebook is ready, on the result screen you can generate a narrated video (voice + illustrated scenes) or a short character animation." },
    ],
    rev_title: "What Families Say", rev_sub: "Stories that became memories forever.",
    reviews: [
      { q: "My son asks to read his book every night. Seeing him as the hero is moving!", name: "Ana C." },
      { q: "I sent a photo and got a beautiful book. It became grandma's birthday gift.", name: "Rafael M." },
      { q: "The illustration looks just like my baby. We'll keep it forever.", name: "Juliana P." },
      { q: "The narrated video moved the whole family. Worth every second.", name: "Marcos & Bia" },
    ],
    features: ["Personalized stories", "Family connection", "Memories that last forever", "An unforgettable gift"],
    band_title: "Ready to Become the Hero?",
    band_sub: "Send your photo and get a unique story, made just for you.",
    band_cta: "Create my account",
    tagline: "Made with love. Created to enchant.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
  es: {
    nav: ["Cómo Funciona", "Libros", "Videos", "FAQ"],
    reviews_link: "Reseñas",
    videos_link: "Videos",
    my_books: "Mis Libros",
    see_all_books: "Ver todos los libros",
    view_all: "Ver todos",
    cat_empty: "Todavía no tenemos un ejemplo de este tema.",
    cats_label: "Libros",
    realistic_link: "Realista",
    cartoon_link: "Libros Cartoon",
    quick_links: "Accesos Rápidos",
    font_label: "Fuente del título",
    explore: "Explorar ahora",
    eyebrow: "Eterniza momentos. Regala a tu familia una historia inolvidable.",
    h_pre: "Convierte una foto en una ", w1: "historia inolvidable", c1: ", donde tu hijo es el ", w2: "protagonista", h_suf: " !",
    lead: "Envías la foto y transformamos a tu hijo en un personaje ilustrado, creando una aventura personalizada especialmente para él — un libro para regalar a la familia y guardar para siempre.",
    cta_login: "Entrar",
    cta_play: "Crear cuenta",
    hero_cta: "Crear mi libro",
    cta_story: "Crear mi historia",
    hero_sign: "Una foto. Una historia. Una memoria eterna.",
    book_carousel: "Carrusel de libros",
    cats: [
      {
        name: "Aventuras",
        subs: ["Aventura", "Dinosaurios", "Fondo del Mar", "Espacio", "Princesas", "Superhéroes", "Deportes"],
        feats: ["Princesas", "Aventura", "Cristobal y su deporte favorito", "Nano y sus aventuras"],
      },
      {
        name: "Tú y Yo",
        subs: ["Mamá y Yo", "Papá y Yo", "Abuela y Yo", "Nuestra Familia", "Hermanos y Primos", "Recién Nacidos", "Boda", "Mascotas"],
        feats: ["Mamá y Yo", "Abuela y Yo", "Nuestra Familia", "El Amor de Mamá"],
      },
      {
        name: "Ocasiones Especiales",
        subs: [
          "Día Internacional de la Mujer · 8 de marzo",
          "Día de la Suegra · 26 de marzo",
          "Pascua",
          "Día de la Madre · 10 de mayo",
          "Día Internacional de la Familia · 15 de mayo",
          "Día del Hermano · 30 de mayo",
          "Día de los Enamorados · 12 de junio",
          "Día del Amigo · 20 de julio",
          "Día de los Abuelos · 26 de julio",
          "Día del Tío y de la Tía · 26 de julio",
          "Día del Padre · 9 de agosto",
          "Día de los Hijos · 11 de agosto",
          "Independencia de Brasil · 7 de septiembre",
          "Día Internacional de las Personas Mayores · 1 de octubre",
          "Día de los Animales · 4 de octubre",
          "Día del Niño · 12 de octubre",
          "Navidad · 25 de diciembre",
          "Cumpleaños",
        ],
        feats: ["Navidad", "Día de la Madre", "Día de los Abuelos", "Día del Padre"],
      },
      {
        name: "Educativo",
        subs: ["Bíblico", "Colores", "Higiene", "Animales", "Sentimientos", "Hora de Dormir", "Compartir", "Cuerpo"],
        feats: ["Animales", "Higiene", "David, el Niño Pastor"],
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
    hiw_title: "Cómo Funciona", hiw_sub: "Tú envías las fotos. Nosotros hacemos el libro, con tu hijo como personaje.",
    hiw: [
      { t: "Envía las fotos", p: "Del niño y de quien más entra en la historia." },
      { t: "Creamos el libro", p: "Un personaje parecido a la foto y una historia solo de ustedes." },
      { t: "El libro queda listo", p: "Páginas ilustradas para leer y guardar." },
    ],
    hiw_main: [
      { t: "Envía la foto del protagonista (original)", p: "Envía fotos nítidas del personaje, protagonista de tu historia." },
      { t: "Envía fotos del personaje adicional", p: "Añade fotos de uno o más personajes relacionadas con la historia que quieres crear." },
      { t: "Revisa y aprueba (portada del libro)", p: "Revisa la vista previa, la portada y las páginas para aprobar. Tras tu confirmación, el libro se envía a producción." },
    ],
    hiw_foot: [
      { t: "Envía la Foto y Define los Detalles", p: "Elige el tema y el formato del libro." },
      { t: "Creamos el Personaje y la Historia", p: "Historia, portada y páginas con el mismo rostro del niño." },
      { t: "Recibes y Apruebas el Libro", p: "Mira la vista previa, aprueba y recibe el libro impreso." },
    ],
    shot_sub: "Envía la foto y define los detalles.",
    shots: [
      { t: "El niño", p: "De 3 a 5 fotos de frente, bien iluminadas, con el rostro completo. Sin filtro, sombrero ni gafas." },
      { t: "Familia y mascotas", p: "2 o 3 fotos de cada persona, sola. De la mascota, una de frente y otra de cuerpo entero." },
      { t: "Datos del libro", p: "Nombre, edad, tema e idioma: portugués, español o inglés." },
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
    vid_title: "Videos Narrados", vid_sub: "La misma historia gana voz, música y movimiento — perfecta para ver en familia.",
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
    cat_title: "Nuestros Libros", cat_sub: "Cada tema se transforma en una historia ilustrada, con tu hijo como protagonista de su propia historia.",
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
      { t: "Miriam y los Secretos del Fondo del Mar", p: "Tortugas, corales y amistad: tu hijo explora el océano con cuidado y encanto.", cover: "Hard", size: "M", tag: "Fondo del Mar", quote: "Cuidar el mar es cuidar a los amigos." },
      { t: "Noé en la Tierra de los Dinosaurios", p: "Fósiles, amigos gigantes y coraje: una expedición prehistórica con tu hijo.", cover: "Hard", size: "M", tag: "Dinosaurios", quote: "Descubrir juntos es la mejor aventura." },
      { t: "El Amor de la Tía", p: "El cariño de la tía en cada página: abrazo, risa y un amor que la familia guarda para siempre.", cover: "Hard", size: "M", tag: "Amor de tía", quote: "El abrazo de la tía no se acaba." },
      { t: "David, el Niño Pastor", p: "Un niño, su arpa y las ovejas: coraje y fe en una historia para guardar para siempre.", cover: "Hard", size: "M", tag: "Fe y coraje", quote: "Pequeño en el campo, grande de corazón." },
      { t: "Mi Papá, Mi Héroe", p: "Papá y el bebé, lado a lado: protección, cariño y un héroe solo de la familia.", cover: "Hard", size: "M", tag: "Papá héroe", quote: "Mi héroe tiene los brazos de papá." },
      { t: "Enzo, Mi Primo Favorito", p: "Dos primos, un abrazo y el mar: amistad que da la familia, para guardar para siempre.", cover: "Hard", size: "M", tag: "Amor de primo", quote: "El primo es el amigo que da la familia." },
      { t: "Lucas y su amigo Max", p: "Un niño y su perro: cuidado, paseos y una amistad para guardar para siempre.", cover: "Hard", size: "M", tag: "Amigo fiel", quote: "Max es el amigo de todas las horas." },
      { t: "Esther y los Superpoderes de la Higiene", p: "Manos limpias, dientes cepillados y una sonrisa: hábitos de higiene que se vuelven superpoderes.", cover: "Hard", size: "M", tag: "Higiene", quote: "Cuidarse es un superpoder." },
      { t: "Pequeño Constructor, Gran Emprendedor", p: "Casco, bloques y un plano en el papel: construir, intentar de nuevo y ver la idea de pie.", cover: "Hard", size: "M", tag: "Construir y crear", quote: "Manos pequeñas, grandes ideas." },
      { t: "Mi Héroe Favorito, el Bombero", p: "Sirena, coraje y un héroe de verdad: el bombero que cuida la ciudad y la familia.", cover: "Hard", size: "M", tag: "Héroes de verdad", quote: "Mi héroe protege a todo el mundo." },
      { t: "Mi Héroe Favorito, el Policía", p: "Uniforme, cuidado y un héroe de la ciudad: el policía que protege a quienes amamos.", cover: "Hard", size: "M", tag: "Héroes de verdad", quote: "Mi héroe cuida de nosotros todos los días." },
      { t: "Mi Héroe Favorito, la Araña", p: "Una tela en el jardín y una amistad pequeña: descubrir la naturaleza con cuidado y encanto.", cover: "Hard", size: "M", tag: "Naturaleza y amistad", quote: "Hasta el amigo más pequeño puede ser un héroe." },
      { t: "Una Tía Especial, No Hay Otra Igual", p: "Paseo, abrazo y risa: la tía que convierte cualquier día en un recuerdo para guardar.", cover: "Hard", size: "M", tag: "Amor de tía", quote: "Con la tía, todo día se vuelve paseo." },
      { t: "El Amor del Abuelo, Mi Puerto Seguro", p: "Los brazos del abuelo, el lago y un abrazo que no se acaba: un puerto seguro solo de la familia.", cover: "Hard", size: "M", tag: "Amor de abuelo", quote: "En los brazos del abuelo, encuentro mi puerto seguro." },
    ],
    promise_title: "Cada Detalle Pensado para Ser Especial",
    promise_sub: "Del envío de la foto a la vista previa, todo está hecho para que el libro quede listo para regalar.",
    promise: [
      { t: "Privacidad de la Foto", p: "La foto que envías se usa solo para crear el libro — nunca para promoción. Los ejemplos de esta página son demostraciones de la plataforma." },
      { t: "Impresión Pensada como Regalo", p: "Preparado para verse hermoso en las manos, en la lectura en familia y al momento de entregarlo." },
      { t: "Vista Previa antes de Avanzar", p: "Ves la portada y las páginas y entiendes lo que estás creando antes de finalizar." },
      { t: "Entrega sin Complicaciones", p: "El PDF queda listo en la plataforma. El libro impreso es bajo consulta — en hasta 24h enviamos la cotización y el plazo." },
    ],
    faq_title: "Preguntas Frecuentes", faq_sub: "Todo lo que necesitas saber.",
    faq: [
      { q: "¿Cómo creo un libro personalizado?", a: "Elige un tema, envía una foto del niño y agrega el nombre y una dedicatoria. La IA transforma la foto en ilustraciones y ves la vista previa antes de finalizar." },
      { q: "¿Puedo ver el libro antes?", a: "¡Sí! Recibes una vista previa completa (portada y páginas) antes de descargar o pedir la impresión." },
      { q: "¿La foto y los datos del niño están seguros?", a: "Sí. Usamos la foto que envías solo para crear el libro y no compartimos tus datos. Los ejemplos de la página inicial son demostraciones, separados de lo que tú envías." },
      { q: "¿Recibo digital o impreso?", a: "El e-book digital queda listo en la plataforma. Si quieres el impreso, pide la cotización después de aprobar el libro." },
      { q: "¿Puedo pedir cambios?", a: "¡Puedes! Ajusta el nombre, la dedicatoria y regenera las ilustraciones en la vista previa hasta que quede a tu gusto." },
      { q: "¿Cómo funciona el video narrado?", a: "Después del ebook listo, en la pantalla de resultado puedes generar el video narrado (voz + escenas ilustradas) o una animación corta del personaje." },
    ],
    rev_title: "Lo que Dicen las Familias", rev_sub: "Historias que se volvieron recuerdos para siempre.",
    reviews: [
      { q: "Mi hijo pide leer su libro todas las noches. ¡Emocionante verlo como héroe!", name: "Ana C." },
      { q: "Envié una foto y recibí un libro hermoso. Se volvió el regalo de cumpleaños de la abuela.", name: "Rafael M." },
      { q: "La ilustración quedó idéntica a mi bebé. Lo vamos a guardar para siempre.", name: "Juliana P." },
      { q: "El video narrado emocionó a toda la familia. Vale cada segundo.", name: "Marcos y Bia" },
    ],
    features: ["Historias personalizadas", "Conexión en familia", "Recuerdos que quedan para siempre", "Un regalo inolvidable"],
    band_title: "¿Listo para Ser el Protagonista?",
    band_sub: "Envía tu foto y recibe una historia única, creada solo para ti.",
    band_cta: "Crear mi cuenta",
    tagline: "Hecho con amor. Creado para encantar.",
    foot_copy: "© 2026 Story R Us — Where Memories Become Magic.",
  },
} as const;

/** "fold" = página dobrando (landing-flip-fold.css). "fade" = esmaecer. */
const FLIP_FX = "fade" as "fade" | "fold";
const FLIP_MS = FLIP_FX === "fold" ? 1100 : 700;
const FLIP_AUTO_MS = 3600;
const FLIP_HOLD_MS = 10000;
const FOLD_N = 2;

function FoldMesh({ src, kind }: { src: string; kind: string }) {
  let node: ReactNode = null;
  for (let i = FOLD_N - 1; i >= 0; i--) {
    node = (
      <div
        className={`fb-seg${i === 0 ? " fb-seg-first" : ""}${i === FOLD_N - 1 ? " fb-seg-last" : ""}`}
        style={{ "--k": String(i / Math.max(1, FOLD_N - 1)) } as CSSProperties}
      >
        <span className="fb-seg-front">
          <img className={`fb-page ${kind}`} src={src} alt="" aria-hidden style={{ left: `${-i * 100}%` }} />
        </span>
        <span className="fb-seg-back" aria-hidden />
        {node}
      </div>
    );
  }
  return (
    <div className="fb-fold" style={{ "--folds": FOLD_N } as CSSProperties} aria-hidden>
      {node}
    </div>
  );
}

function prefersReducedMotion() {
  try {
    return !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

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
  const [paused, setPaused] = useState(false);
  const busy = useRef(false);
  const fromSelf = useRef(false);
  const didMount = useRef(false);
  const holdUntil = useRef(0);
  const indexRef = useRef(index);
  const onIndexRef = useRef(onIndex);
  const pagesRef = useRef(pages);
  indexRef.current = index;
  onIndexRef.current = onIndex;
  pagesRef.current = pages;
  const pageSrc = pages[index];
  const pageKey = pages.join("|");
  useEffect(() => {
    pages.forEach((src) => {
      const img = new Image();
      img.src = exUrl(src);
    });
  }, [pageKey]);
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
  useEffect(() => {
    if (!didMount.current) {
      didMount.current = true;
      setTarget(index);
      return;
    }
    if (fromSelf.current) {
      fromSelf.current = false;
      return;
    }
    busy.current = false;
    setAnim(null);
    setTarget(index);
    holdUntil.current = Date.now() + FLIP_HOLD_MS;
  }, [index]);
  const commit = (next: number) => {
    fromSelf.current = true;
    onIndexRef.current(next);
  };
  const finish = (next: number) => {
    if (!busy.current) return;
    busy.current = false;
    setAnim(null);
    commit(next);
  };
  const flip = (dir: "next" | "prev", fromUser = false) => {
    const list = pagesRef.current;
    if (busy.current || list.length < 2) return;
    const cur = indexRef.current;
    const next = dir === "next" ? (cur + 1) % list.length : (cur - 1 + list.length) % list.length;
    if (fromUser) holdUntil.current = Date.now() + FLIP_HOLD_MS;
    if (prefersReducedMotion()) {
      commit(next);
      return;
    }
    busy.current = true;
    setTarget(next);
    setAnim(dir);
  };
  useEffect(() => {
    if (pages.length < 2) return;
    const tick = () => {
      if (busy.current || paused || document.hidden) return;
      if (Date.now() < holdUntil.current) return;
      flip("next");
    };
    const id = window.setInterval(tick, FLIP_AUTO_MS);
    return () => window.clearInterval(id);
  }, [pageKey, paused]);
  const onLeafEnd = (e: { animationName?: string; target?: EventTarget; currentTarget?: EventTarget }) => {
    if (!anim) return;
    if (e.target !== e.currentTarget) return;
    if (e.animationName && !/^(fbPeel|fbFade)/.test(e.animationName)) return;
    finish(target);
  };
  useEffect(() => {
    if (!anim) return;
    const id = window.setTimeout(() => finish(target), FLIP_MS + 80);
    return () => window.clearTimeout(id);
  }, [anim, target]);
  const folding = FLIP_FX === "fold";
  const underSrc = folding
    ? (anim === "next" ? pages[target] : pages[index])
    : (anim ? pages[target] : pages[index]);
  const leafSrc = folding
    ? (anim === "next" ? pages[index] : (anim === "prev" ? pages[target] : pages[index]))
    : pages[index];
  const underIdx = folding
    ? (anim === "next" ? target : index)
    : (anim ? target : index);
  const leafIdx = folding
    ? (anim === "next" ? index : (anim === "prev" ? target : index))
    : index;
  const pageKind = (idx: number) => {
    if (idx === 0) return "fb-page--cover";
    if (idx === pages.length - 1) return "fb-page--photo";
    return "fb-page--spread";
  };
  const pageLabel = (idx: number) => {
    if (idx === 0) return labels.cover;
    if (idx === pages.length - 1) return labels.photo;
    return labels.turn;
  };
  const single = pages.length < 2;
  const onStage = (e: RMouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (e.clientX - r.left > r.width / 2) flip("next", true); else flip("prev", true);
  };
  const onStageKey = (e: RKeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") {
      e.preventDefault();
      flip("next", true);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      flip("prev", true);
    }
  };
  const goTo = (i: number) => {
    if (i === index || busy.current) return;
    const wrapNext = index === pages.length - 1 && i === 0;
    const wrapPrev = index === 0 && i === pages.length - 1;
    const step = Math.abs(i - index) === 1 || wrapNext || wrapPrev;
    if (step) {
      flip(wrapPrev || i < index ? "prev" : "next", true);
      return;
    }
    holdUntil.current = Date.now() + FLIP_HOLD_MS;
    commit(i);
  };
  return (
    <div
      className="flipbook"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setPaused(false);
      }}
    >
      <div className="fb-board">
        {single ? null : <button className="fb-nav" type="button" onClick={() => flip("prev", true)} disabled={!!anim} aria-label={labels.prev}>‹</button>}
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
          <span className="fb-under-shade" aria-hidden />
          <div
            className={`fb-leaf fb-fx-${FLIP_FX}${anim ? ` ${anim}` : ""}`}
            onAnimationEnd={(e) => onLeafEnd(e)}
          >
            <img className={`fb-page fb-leaf-front ${pageKind(leafIdx)}`} src={exUrl(leafSrc)} alt={pageLabel(index)} data-testid="landing-hero-flip" />
            {folding ? <FoldMesh src={exUrl(leafSrc)} kind={pageKind(leafIdx)} /> : null}
            {folding ? <span className="fb-leaf-back" aria-hidden /> : null}
            {folding ? <span className="fb-leaf-shade" aria-hidden /> : null}
          </div>
        </div>
        {single ? null : <button className="fb-nav" type="button" onClick={() => flip("next", true)} disabled={!!anim} aria-label={labels.next}>›</button>}
      </div>
      {single ? null : (
        <div className="fb-dots" role="tablist" aria-label={labels.turn}>
          {pages.map((_, i) => (
            <button
              key={pages[i]}
              type="button"
              className={`fb-dot${i === index ? " on" : ""}`}
              role="tab"
              aria-selected={i === index}
              aria-label={pageLabel(i)}
              data-testid={`landing-hero-flip-dot-${i}`}
              onClick={() => goTo(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// M R$ 177 e P R$ 157. Inglês em dólar e espanhol em euro (câmbio de 2 out 2026: USD 5,22 e EUR 5,88).
const FORMAT_COPY: Record<Lang, {
  pages: string;
  hard: string;
  soft: string;
  sizeM: string;
  sizeP: string;
  priceM: string;
  priceP: string;
  hardText: string;
  softText: string;
}> = {
  pt: {
    pages: "Livro 16 páginas",
    hard: "HARD",
    soft: "SOFT",
    sizeM: "20 × 20 cm",
    sizeP: "15 × 15 cm",
    priceM: "R$ 177,00",
    priceP: "R$ 157,00",
    hardText: "Resistente e durável. Utilizada em edições especiais ou colecionáveis.",
    softText: "Leve e flexível. Comum em livros e edições econômicas.",
  },
  en: {
    pages: "Book. 16 pages.",
    hard: "HARD",
    soft: "SOFT",
    sizeM: "20 × 20 cm",
    sizeP: "15 × 15 cm",
    priceM: "$33.91",
    priceP: "$30.08",
    hardText: "Sturdy and durable. Used for special or collectible editions.",
    softText: "Light and flexible. Common in books and economical editions.",
  },
  es: {
    pages: "Libro. 16 páginas.",
    hard: "HARD",
    soft: "SOFT",
    sizeM: "20 × 20 cm",
    sizeP: "15 × 15 cm",
    priceM: "30,10 €",
    priceP: "26,70 €",
    hardText: "Resistente y duradera. Utilizada en ediciones especiales o de colección.",
    softText: "Ligera y flexible. Común en libros y ediciones económicas.",
  },
};
export type CatalogCardBook = {
  t: string;
  img: string;
  theme: string;
  cover?: string;
  size?: string;
  tag?: string;
  heroi?: string;
  catalogI?: number;
  story?: string;
  quote?: string;
};
const BOOK_PAGE_COPY: Record<Lang, { summary: string; details: string }> = {
  pt: { summary: "Resumo da história", details: "Detalhes do livro" },
  en: { summary: "Story summary", details: "Book details" },
  es: { summary: "Resumen de la historia", details: "Detalles del libro" },
};
export function CatalogBookCard({
  book,
  lang,
  personalize,
  modo = "realista",
  linkBook = true,
  showStory = false,
  layout = "card",
}: {
  book: CatalogCardBook;
  lang: Lang;
  personalize: string;
  modo?: "realista" | "cartoon";
  linkBook?: boolean;
  showStory?: boolean;
  layout?: "card" | "page";
}) {
  const [cover, setCover] = useState<CatalogCoverChoice>(catalogCoverChoice(book.cover));
  const [size, setSize] = useState<CatalogSizeChoice>(catalogSizeChoice(book.size));
  const copy = FORMAT_COPY[lang];
  const bookHref = book.catalogI != null ? `/livro/${book.catalogI}` : null;
  const linked = linkBook && bookHref != null;
  const image = <img src={exUrl(book.img)} alt={book.t} loading="lazy" />;
  const notes = (
    <div className="cat-notes">
      <div className="cat-notes-sizes">
        <p className="cat-notes-lead">{copy.pages}</p>
        {(["P", "M"] as const).map((choice) => (
          <p key={choice} className="cat-note-line">
            <span className="cat-opt">
              <button
                type="button"
                className={size === choice ? "is-on" : ""}
                aria-pressed={size === choice}
                onClick={() => setSize(choice)}
              >
                {choice}
              </button>
            </span>
            <span>
              {choice === "M" ? copy.sizeM : copy.sizeP}:{" "}
              <span className={size === choice ? "is-price" : undefined}>
                {choice === "M" ? copy.priceM : copy.priceP}.
              </span>
            </span>
          </p>
        ))}
      </div>
      <div className="cat-note-grid">
        {(["hard", "soft"] as const).map((choice) => (
          <div key={choice} className="cat-note-line">
            <span className="cat-opt">
              <button
                type="button"
                className={cover === choice ? "is-on" : ""}
                aria-pressed={cover === choice}
                onClick={() => setCover(choice)}
              >
                {choice === "hard" ? copy.hard : copy.soft}
              </button>
            </span>
            <p>{choice === "hard" ? copy.hardText : copy.softText}</p>
          </div>
        ))}
      </div>
    </div>
  );
  const go = (
    <Link
      to={personalizeHref({
        theme: book.theme,
        title: book.t,
        historia: book.tag,
        heroi: book.heroi,
        size,
        cover,
        modo: modo ?? "realista",
        catalogI: book.catalogI,
      })}
      className="kbtn kbtn-primary cat-go"
      data-testid="landing-personalize"
    >
      {personalize}
    </Link>
  );
  if (layout === "page") {
    const pageCopy = BOOK_PAGE_COPY[lang];
    return (
      <article className="cat-card book-sheet reveal" data-testid="landing-catalog-card" data-format="catalog">
        <div className="cat-display">
          <div className="cat-book">{image}</div>
        </div>
        <div className="cat-body">
          {book.tag ? <p className="book-tag">{book.tag}</p> : null}
          <h1>{book.t}</h1>
          <section className="book-block">
            <h2>{pageCopy.summary}</h2>
            {book.story ? <p className="cat-story" data-testid="book-story">{book.story}</p> : null}
            {book.quote ? <p className="cat-quote">{book.quote}</p> : null}
          </section>
          <section className="book-block">
            <h2>{pageCopy.details}</h2>
            {notes}
          </section>
          {go}
        </div>
      </article>
    );
  }
  return (
    <div className="cat-card" data-testid="landing-catalog-card" data-format="catalog">
      <div className="cat-display">
        <div className="cat-book">
          {linked ? <Link to={bookHref} className="cat-book-link">{image}</Link> : image}
        </div>
      </div>
      <div className="cat-body">
        <h3>{linked ? <Link to={bookHref}>{book.t}</Link> : book.t}</h3>
        {showStory && book.story ? <p className="cat-story" data-testid="book-story">{book.story}</p> : null}
        {showStory && book.quote ? <p className="cat-quote">{book.quote}</p> : null}
        {notes}
        {go}
      </div>
    </div>
  );
}
function toCatalogCard(lang: Lang, index: number): CatalogCardBook | null {
  if (index === 13) return null;
  const book = I18N[lang].catalog[index];
  const theme = CATALOG_THEMES[index];
  if (!book || !theme || !CATALOG_IMGS[index]) return null;
  return {
    t: book.t,
    story: book.p,
    quote: book.quote,
    img: catalogCoverFile(index, lang, "photo"),
    theme,
    cover: book.cover,
    size: book.size,
    tag: book.tag,
    heroi: HERO_BY_CATALOG[index],
    catalogI: index,
  };
}
export function readSiteLang(): Lang {
  try {
    const s = localStorage.getItem("lang");
    if (s === "pt" || s === "en" || s === "es") return s;
  } catch { /* ignore */ }
  return "pt";
}
export function catalogPageCopy(lang: Lang) {
  const t = I18N[lang];
  return {
    title: t.cat_title,
    personalize: t.personalize,
    back: t.see_all_books,
    empty: t.cat_empty,
    cats: t.cats_label,
    hiw: t.hiw_title,
    videos: t.videos_link,
    reviews: t.reviews_link,
    cartoon: t.cartoon_link,
  };
}
export function catalogCategory(lang: Lang, id: string) {
  if (id === "sentimentos") {
    const name = lang === "en" ? "Feelings" : lang === "es" ? "Sentimientos" : "Sentimentos";
    return {
      id,
      name,
      color: "#f0a0c0",
      books: CATALOG_THEMES.flatMap((theme, index) => {
        if (!FEELING_THEMES.has(theme)) return [];
        const card = toCatalogCard(lang, index);
        return card ? [card] : [];
      }),
    };
  }
  return catalogSections(lang).find((section) => section.id === id) ?? null;
}
export function catalogEntry(lang: Lang, index: number) {
  const card = toCatalogCard(lang, index);
  if (!card) return null;
  const section = NAV_CAT_META.find((meta) => CATALOG_SECTION_THEMES[meta.id]?.includes(card.theme));
  return { ...card, sectionId: section?.id ?? "aventuras" };
}
export function catalogSections(lang: Lang) {
  const names = I18N[lang].cats;
  return NAV_CAT_META.map((meta, i) => ({
    id: meta.id,
    name: names[i]?.name ?? meta.id,
    color: meta.color,
    books: CATALOG_THEMES.flatMap((theme, index) => {
      if (!CATALOG_SECTION_THEMES[meta.id]?.includes(theme)) return [];
      const card = toCatalogCard(lang, index);
      return card ? [card] : [];
    }).sort((a, b) => {
      const rank = (i: number) => {
        const lead = CATALOG_LEAD.indexOf(i);
        return lead === -1 ? CATALOG_LEAD.length + i : lead;
      };
      return rank(a.catalogI ?? Number.MAX_SAFE_INTEGER) - rank(b.catalogI ?? Number.MAX_SAFE_INTEGER);
    }),
  }));
}

export function Landing({ variant = "photo" }: { variant?: "photo" | "cartoon" } = {}) {
  const rootRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [openCat, setOpenCat] = useState<number | null>(null);
  const [subHover, setSubHover] = useState<{ cat: number; sub: number } | null>(null);
  const [featCat, setFeatCat] = useState<number | null>(null);
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
  const hiwSteps = t.hiw_main;
  const howImgs = variant === "cartoon" ? HOW_IMGS : HOW_SCENE_IMGS;
  const navHrefs = ["#como", "#catalogo", "#videos", "#faq"];
  const heroStrip = HERO_STRIP.flatMap((book) => {
    if (variant !== "cartoon") return [book];
    const shot = CARTOON_HERO[book.name];
    if (!shot) return [];
    return [{
      ...book,
      cover: shot.cover ? heroAsset(shot.cover) : book.cover,
      page: shot.page ? heroAsset(shot.page) : book.page,
      photo: shot.photo ? heroAsset(shot.photo) : book.photo,
    }];
  });
  const catalogBooks = t.catalog
        .map((c, i) => ({ c, i }))
        .filter(({ i }) => (variant === "cartoon"
          ? Boolean(CARTOON_COVER[i])
          : (CATALOG_NEW_INDEXES.has(i) || i < CATALOG_LIMIT) && !CATALOG_CARTOON_INDEXES.has(i)))
        .sort((a, b) => {
          const rank = (i: number) => {
            const lead = CATALOG_LEAD.indexOf(i);
            return lead === -1 ? CATALOG_LEAD.length + i : lead;
          };
          return rank(a.i) - rank(b.i);
        })
        .map(({ c, i }) => ({
          t: c.t,
          img: catalogCoverFile(i, lang, variant),
          theme: CATALOG_THEMES[i],
          cover: c.cover,
          size: c.size,
          tag: c.tag,
          heroi: HERO_BY_CATALOG[i],
          catalogI: i,
        }));
  const reviewPhotos = variant === "cartoon" ? CARTOON_REVIEW_PHOTOS : REVIEW_PHOTOS;
  const heroSeries = Math.min(Math.floor(heroPick / 3), Math.max(heroStrip.length - 1, 0));
  const heroPage = heroPick % 3;
  const heroBook = heroStrip[heroSeries] ?? heroStrip[0];
  const heroPages = [heroBook.cover[lang], heroBook.page[lang], heroBook.photo[lang]];
  const flipLabels = { prev: t.fb_prev, next: t.fb_next, turn: t.fb_turn, cover: t.fb_cover, photo: t.fb_photo };
  const bookStudioHref = (theme: string, catalogI?: number) => {
    if (catalogI === undefined) return accountGateHref(`/app?tema=${theme}`);
    const book = t.catalog[catalogI];
    if (!book) return accountGateHref(`/app?tema=${theme}`);
    return studioHref({
      tema: theme,
      titulo: book.t,
      historia: `${book.tag}. ${book.p}`,
      heroi: HERO_BY_CATALOG[catalogI],
      cover: catalogCoverChoice(book.cover),
      modo: variant === "cartoon" ? "cartoon" : "realista",
      catalogI,
    });
  };
  const navCats = t.cats.map((cat, i) => ({
    ...cat,
    id: NAV_CAT_META[i].id,
    color: NAV_CAT_META[i].color,
    subs: cat.subs.flatMap((label, j) => {
      const meta = NAV_CAT_META[i].subs[j];
      const when = "when" in meta ? meta.when : undefined;
      if (when && !occasionDue(when, new Date())) return [];
      const theme = themeFromHref(meta.href);
      const rawOnly = theme && MENU_BOOKS[theme]?.length === 1 ? MENU_BOOKS[theme][0] : undefined;
      const only = rawOnly !== undefined && (variant !== "cartoon" || CARTOON_COVER[rawOnly]) ? rawOnly : undefined;
      const bookTheme = only !== undefined ? CATALOG_THEMES[only] ?? theme : theme;
      return [{
        label,
        href: bookTheme ? bookStudioHref(bookTheme, only) : accountGateHref(meta.href),
        due: when ? nextOccasionDate(when, new Date()) : null,
      }];
    }).sort((a, b) => {
      if (a.due && b.due) return a.due.getTime() - b.due.getTime();
      if (a.due) return -1;
      if (b.due) return 1;
      return 0;
    }),
    feats: cat.feats.flatMap((label, j) => {
      const meta = NAV_CAT_META[i].feats[j];
      if (variant === "cartoon" && !CARTOON_COVER[meta.catalogI]) return [];
      return [{
        label,
        href: `/livro/${meta.catalogI}`,
        img: catalogCoverFile(meta.catalogI, lang, variant),
      }];
    }).slice(0, 4),
  }));
  const voceEeuCount = navCats.find((cat) => cat.id === "voce-e-eu")?.subs.length ?? 0;
  const menuCats = navCats.map((cat) => {
    if (cat.id !== "ocasioes" || cat.subs.length <= voceEeuCount) return cat;
    const open = cat.subs.filter((sub) => !sub.due);
    const dated = cat.subs.filter((sub) => sub.due);
    const room = Math.max(voceEeuCount - open.length, 0);
    return { ...cat, subs: [...dated.slice(0, room), ...open].slice(0, voceEeuCount) };
  });
  const shownCats = menuCats;
  const menuBooks = (theme: string) => (MENU_BOOKS[theme] ?? []).flatMap((i) => {
    if (variant === "cartoon" && !CARTOON_COVER[i]) return [];
    const book = t.catalog[i];
    const img = CATALOG_IMGS[i];
    if (!book || !img) return [];
    return [{ label: book.t, href: `/livro/${i}`, img: catalogCoverFile(i, lang, variant) }];
  }).slice(0, 4);

  const featIcons = [IcSparkle, IcHeart, IcBook, IcGift];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch { /* ignore */ }
  }, [theme]);

  useEffect(() => {
    const id = window.location.hash.replace("#", "");
    const el = id ? document.getElementById(id) : null;
    if (!el) return;
    const offset = (headerRef.current?.getBoundingClientRect().height ?? 0) + 12;
    const top = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top });
  }, []);

  useEffect(() => {
    const header = headerRef.current;
    const root = rootRef.current;
    if (!header || !root) return;
    const sync = () => {
      root.style.setProperty("--khead-h", `${Math.ceil(header.getBoundingClientRect().height)}px`);
    };
    sync();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(sync);
    observer.observe(header);
    return () => observer.disconnect();
  }, []);

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
        setSubHover(null);
        setFeatCat(null);
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
      setSubHover(null);
      setFeatCat(null);
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
    setSubHover(null);
    setFeatCat(null);
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
                <div
                  className={`kcat${openCat === 0 ? " open" : ""}`}
                  onMouseEnter={() => setOpenCat(0)}
                  onMouseLeave={() => { setOpenCat(null); setSubHover(null); setFeatCat(null); }}
                >
                  <button
                    type="button"
                    className="kcat-btn"
                    style={{ "--cat": "#9b8cff" } as CSSProperties}
                    aria-expanded={openCat === 0}
                    aria-haspopup="true"
                    aria-controls="cat-panel"
                    onClick={() => setOpenCat(openCat === 0 ? null : 0)}
                  >
                    <span className="kcat-dot" style={{ background: "#9b8cff", boxShadow: "0 0 10px #9b8cff" }} />
                    {t.cats_label}
                  </button>
                  <div className="kcat-panel kcat-panel-all" id="cat-panel">
                    <div className="kcat-groups">
                      {shownCats.map((cat, i) => (
                        <div
                          key={cat.id}
                          className="kcat-group"
                          style={{ "--group": cat.color } as CSSProperties}
                          onMouseEnter={() => {
                            setFeatCat(i);
                            setSubHover((cur) => (cur?.cat === i ? cur : null));
                          }}
                        >
                          <Link to={`/catalogo/${cat.id}`} className="kcat-group-name is-chip" onClick={closeNav}>
                            <span className="kcat-dot" style={{ background: cat.color, boxShadow: `0 0 8px ${cat.color}` }} />
                            {cat.name}
                          </Link>
                          <ul className="kcat-subs">
                            {cat.subs.map((sub, j) => (
                              <li key={sub.label} className={subHover?.cat === i && subHover.sub === j ? "on" : ""}>
                                <Link
                                  to={sub.href}
                                  onClick={closeNav}
                                  onMouseEnter={() => setSubHover({ cat: i, sub: j })}
                                  onFocus={() => setSubHover({ cat: i, sub: j })}
                                ><SubLabel label={sub.label} /></Link>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                    <div className="kcat-feats" data-testid="landing-cat-feats">
                      {(() => {
                        const hoverCat = subHover ? shownCats[subHover.cat] : featCat != null ? shownCats[featCat] : null;
                        const activeSub = subHover && hoverCat ? hoverCat.subs[subHover.sub] : null;
                        const activeTheme = activeSub ? themeFromHref(activeSub.href) : null;
                        const shown = (activeTheme ? menuBooks(activeTheme) : hoverCat?.feats ?? []).slice(0, 4);
                        const allHref = hoverCat ? `/catalogo/${hoverCat.id}` : "/catalogo";
                        return (
                          <>
                            {shown.map((feat) => (
                              <Link key={`${feat.href}-${feat.label}`} className="kcat-feat" to={feat.href} onClick={closeNav}>
                                <span className="kcat-feat-cover">
                                  <img src={exUrl(feat.img)} alt="" />
                                </span>
                                <span>{feat.label}</span>
                              </Link>
                            ))}
                            {activeTheme && shown.length === 0 ? <p className="kcat-empty">{t.cat_empty}</p> : null}
                            <Link to={allHref} className="kbtn kbtn-go kcat-all" onClick={closeNav}>{t.view_all}</Link>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                </div>
                <a href="#como" className="kcat-btn" style={{ "--cat": "#7aa2ff" } as CSSProperties} onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#7aa2ff", boxShadow: "0 0 10px rgba(122,162,255,.9)" }} />
                  {t.hiw_title}
                </a>
                <Link to={variant === "cartoon" ? "/" : "/cartoon"} className="kcat-btn" style={{ "--cat": variant === "cartoon" ? "#7aa2ff" : "#3ecf8e" } as CSSProperties} onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: variant === "cartoon" ? "#7aa2ff" : "#3ecf8e", boxShadow: variant === "cartoon" ? "0 0 10px rgba(122,162,255,.95)" : "0 0 10px rgba(62,207,142,.95)" }} />
                  {variant === "cartoon" ? t.realistic_link : t.cartoon_link}
                </Link>
                <a href="#videos" className="kcat-btn" style={{ "--cat": "#e07a9a" } as CSSProperties} onClick={closeNav}>
                  <span className="kcat-dot" style={{ background: "#e07a9a", boxShadow: "0 0 10px rgba(224,122,154,.9)" }} />
                  {t.videos_link}
                </a>
                <a href="#reviews" className="kcat-btn" style={{ "--cat": "#f4b740" } as CSSProperties} onClick={closeNav}>
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
            <div className="khead-links" data-testid="landing-header-auth">
              <Link to="/entrar" className="kbtn kbtn-login" data-testid="landing-header-login">{t.cta_login}</Link>
              <Link to="/cadastro" className="kbtn kbtn-primary" data-testid="landing-header-cta">{t.cta_play}</Link>
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
            {shownCats.map((cat, i) => (
              <div key={cat.id} className={`kmobile-cat${mobileCat === i ? " open" : ""}`} style={{ "--group": cat.color } as CSSProperties}>
                <div className="kmobile-cat-btn">
                  <Link to={`/catalogo/${cat.id}`} onClick={closeNav}>
                    <span className="kcat-dot" style={{ background: cat.color }} />
                    {cat.name}
                  </Link>
                  <button
                    type="button"
                    className="kmobile-cat-toggle"
                    aria-expanded={mobileCat === i}
                    aria-controls={`mobile-cat-${i}`}
                    aria-label={cat.name}
                    onClick={() => setMobileCat(mobileCat === i ? null : i)}
                  >
                    <IcChevron className="faq-chev" />
                  </button>
                </div>
                <div className="kmobile-subs" id={`mobile-cat-${i}`}>
                  <div className="kmobile-subs-inner">
                    {cat.subs.map((sub) => (
                      <Link key={sub.label} to={sub.href} onClick={closeNav}><SubLabel label={sub.label} /></Link>
                    ))}
                  </div>
                </div>
              </div>
            ))}
            <Link to="/catalogo" className="kmobile-all" onClick={closeNav}>{t.view_all}</Link>
          </div>
          <div className="kmobile-section">
            <p className="kmobile-label">{t.quick_links}</p>
            <a className="kmobile-link" href="#como" onClick={closeNav}>{t.hiw_title}</a>
            <Link className="kmobile-link" to={variant === "cartoon" ? "/" : "/cartoon"} onClick={closeNav}>{variant === "cartoon" ? t.realistic_link : t.cartoon_link}</Link>
            <a className="kmobile-link" href="#videos" onClick={closeNav}>{t.videos_link}</a>
            <a className="kmobile-link" href="#reviews" onClick={closeNav}>{t.reviews_link}</a>
            <a className="kmobile-link" href="#catalogo" onClick={closeNav}>{t.nav[1]}</a>
            <a className="kmobile-link" href="#faq" onClick={closeNav}>{t.nav[3]}</a>
          </div>
          <div className="kmobile-auth" data-testid="landing-mobile-auth">
            <Link to="/entrar" className="kbtn kbtn-login" data-testid="landing-mobile-login" onClick={closeNav}>{t.cta_login}</Link>
            <Link to="/cadastro" className="kbtn kbtn-primary" data-testid="landing-mobile-cta" onClick={closeNav}>{t.cta_play}</Link>
          </div>
        </nav>
        </div>
      </header>

      {/* HERO — proposta de valor + faixa de livros */}
      <section className="kbanner-hero" aria-label={t.hero_sign}>
        <div className="khero-intro">
          <h1>{t.h_pre}<em className="g1">{t.w1}</em>{t.c1}<em className="g2">{t.w2}</em>{t.h_suf}</h1>
          <span className="keyebrow"><IcSparkle className="ei" /> {t.hero_sign}</span>
        </div>
        <div className="hero-carousel" aria-label={t.book_carousel}>
          <div className="hero-carousel-track">
            {[0, 1].map((copy) => heroStrip.map((book, seriesIndex) => {
              const shots = [book.cover[lang], book.page[lang], book.photo[lang]];
              const seriesOn = Math.floor(heroPick / 3) === seriesIndex;
              return (
                <div
                  className={`hero-slide${seriesOn ? " on" : ""}${seriesIndex === 0 ? " is-lead" : ""}`}
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
            key={`${heroBook.name}-${lang}`}
            pages={heroPages}
            index={heroPage}
            onIndex={(next) => setHeroPick(heroSeries * 3 + next)}
            labels={flipLabels}
          />
        </div>
        <div className="khero-after">
          <span className="keyebrow"><IcSparkle className="ei" /> {t.eyebrow}</span>
          <Link to="/cadastro" className="kbtn kbtn-primary" data-testid="landing-hero-cta">{t.hero_cta}</Link>
        </div>
      </section>

      {/* COMO FUNCIONA + DICAS */}
      <section className="ksection ksection-como" id="como">
        <div className="como-panel reveal">
          <h2 className="ktitle">{t.hiw_title}</h2>
          <div className="howex">
            {hiwSteps.map((h, i) => {
              return (
              <Fragment key={h.t}>
                <figure className="howex-card howex-card-scene">
                  <div className="howex-lead">
                    <h3>{h.t}</h3>
                  </div>
                  <div className="howex-media">
                    <img src={exUrl(howImgs[i])} alt={h.t} loading="lazy" />
                    <span className="howex-num">{i + 1}</span>
                  </div>
                  <figcaption>
                    <p>{h.p}</p>
                  </figcaption>
                </figure>
                {i < hiwSteps.length - 1 && <span className="howex-arrow" aria-hidden><IcArrow /></span>}
              </Fragment>
              );
            })}
          </div>
        </div>
      </section>

      {/* NOSSOS LIVROS */}
      <section className="ksection" id="catalogo">
        <h2 className="ktitle reveal">{t.cat_title}</h2>
        <p className="ksub reveal">{t.cat_sub}</p>
        <div className="cat-grid">
          {catalogBooks.map((c) => (
            <CatalogBookCard
              key={c.t}
              book={c}
              lang={lang}
              personalize={t.personalize}
              modo={variant === "cartoon" ? "cartoon" : "realista"}
            />
          ))}
        </div>
      </section>

      {/* NOSSA PROMESSA — logo abaixo dos livros */}
      <section className="ksection promise-section" id="promessa">
        <h2 className="ktitle reveal promise-heading">
          {lang === "pt" ? (
            <>
              Um <span className="promise-mark">Presente</span> Personalizado para Eternizar Momentos Inesquecíveis.
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
        <div className="vid-cta"><Link to="/cadastro" className="kbtn kbtn-primary big">{t.vid_cta}</Link></div>
      </section>

      {/* AVALIAÇÕES */}
      <section className="ksection" id="reviews">
        <h2 className="ktitle reveal">{t.rev_title}</h2>
        <p className="ksub reveal">{t.rev_sub}</p>
        <div className="rev-carousel reveal" aria-label={t.rev_title}>
          <div className="rev-carousel-track">
            {[0, 1].map((copy) => reviewPhotos.map((b, i) => (
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
        <Link to="/cadastro" className="kbtn kbtn-primary big">{t.band_cta}</Link>
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
