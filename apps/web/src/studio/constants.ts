import type { Theme } from "../types";
import type { StudioCopy } from "./i18n";

export const ART_STYLE_KEY = "realistic" as const;

/** Temas narrativos do briefing — a história nasce ao redor do tema escolhido. */
export type ThemeGroup = "aventura" | "datas" | "educativo";

export const THEMES: { id: Theme; emoji: string; group: ThemeGroup }[] = [
  // Aventura e fantasia
  { id: "adventure", emoji: "🗺️", group: "aventura" },
  { id: "princess", emoji: "👑", group: "aventura" },
  { id: "superhero", emoji: "🦸", group: "aventura" },
  { id: "space", emoji: "🚀", group: "aventura" },
  { id: "underwater", emoji: "🐠", group: "aventura" },
  { id: "dinosaurs", emoji: "🦕", group: "aventura" },
  { id: "fantasy", emoji: "🧚", group: "aventura" },
  // Datas comemorativas
  { id: "birthday", emoji: "🎂", group: "datas" },
  { id: "christmas", emoji: "🎄", group: "datas" },
  { id: "easter", emoji: "🐣", group: "datas" },
  { id: "childrens_day", emoji: "🎈", group: "datas" },
  { id: "mothers_day", emoji: "💐", group: "datas" },
  { id: "fathers_day", emoji: "👔", group: "datas" },
  { id: "new_year", emoji: "🎉", group: "datas" },
  // Temas educativos — Linguagem & Conceitos Fundamentais
  { id: "alfabetizacao_inicial", emoji: "🔤", group: "educativo" },
  { id: "pensamento_matematico", emoji: "🔢", group: "educativo" },
  { id: "cores", emoji: "🎨", group: "educativo" },
  { id: "opostos_espacial", emoji: "↕️", group: "educativo" },
  // Temas educativos — Habilidades de Vida & Rotinas Diárias
  { id: "higiene_desfralde", emoji: "🧼", group: "educativo" },
  { id: "rotina_dormir", emoji: "🌙", group: "educativo" },
  { id: "alimentacao_saudavel", emoji: "🥗", group: "educativo" },
  { id: "vestir_autonomia", emoji: "👕", group: "educativo" },
  // Temas educativos — Autoconsciência & Aprendizagem Socioemocional
  { id: "literacia_emocional", emoji: "💗", group: "educativo" },
  { id: "consciencia_corporal", emoji: "🙆", group: "educativo" },
  { id: "compartilhar_revezar", emoji: "🤝", group: "educativo" },
  // Temas educativos — Descoberta & Exploração do Mundo
  { id: "animais_sons", emoji: "🐾", group: "educativo" },
  { id: "transporte_ajudantes", emoji: "🚚", group: "educativo" },
  { id: "clima_estacoes", emoji: "⛅", group: "educativo" },
];

export const resolveThemeName = (
  id: string | null | undefined,
  themes: StudioCopy["themes"],
  empty = "—",
) => (id && id in themes ? themes[id as Theme] : empty);

/** Etapas finais (dependem de personagem + história). */
export function studioSteps(t: StudioCopy): {
  key: "ebook" | "video" | "narrated-video";
  label: string;
  cost: string;
  hint: string;
}[] {
  return [
    {
      key: "ebook",
      label: t.stepEbook,
      cost: t.stepEbookCost,
      hint: t.stepEbookHint,
    },
    {
      key: "video",
      label: t.stepVideo,
      cost: t.stepVideoCost,
      hint: t.stepVideoHint,
    },
    {
      key: "narrated-video",
      label: t.stepNarrated,
      cost: t.stepNarratedCost,
      hint: t.stepNarratedHint,
    },
  ];
}
