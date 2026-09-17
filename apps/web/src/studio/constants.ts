import type { Theme } from "../types";

export const ART_STYLE_LABEL: Record<string, string> = {
  cgi_3d: "Rosto realista",
  realistic: "Rosto realista",
  cartoon: "Rosto realista",
  anime: "Rosto realista",
};

/** Temas narrativos do briefing — a história nasce ao redor do tema escolhido. */
export type ThemeGroup = "aventura" | "datas" | "educativo";

export const THEMES: { id: Theme; label: string; emoji: string; group: ThemeGroup }[] = [
  // Aventura e fantasia
  { id: "adventure", label: "Aventura", emoji: "🗺️", group: "aventura" },
  { id: "princess", label: "Princesas", emoji: "👑", group: "aventura" },
  { id: "superhero", label: "Super-heróis", emoji: "🦸", group: "aventura" },
  { id: "space", label: "Espaço", emoji: "🚀", group: "aventura" },
  { id: "underwater", label: "Fundo do mar", emoji: "🐠", group: "aventura" },
  { id: "dinosaurs", label: "Dinossauros", emoji: "🦕", group: "aventura" },
  { id: "fantasy", label: "Fantasia", emoji: "🧚", group: "aventura" },
  // Datas comemorativas
  { id: "birthday", label: "Aniversário", emoji: "🎂", group: "datas" },
  { id: "christmas", label: "Natal", emoji: "🎄", group: "datas" },
  { id: "easter", label: "Páscoa", emoji: "🐣", group: "datas" },
  { id: "childrens_day", label: "Dia das Crianças", emoji: "🎈", group: "datas" },
  { id: "mothers_day", label: "Dia das Mães", emoji: "💐", group: "datas" },
  { id: "fathers_day", label: "Dia dos Pais", emoji: "👔", group: "datas" },
  { id: "new_year", label: "Ano Novo", emoji: "🎉", group: "datas" },
  // Temas educativos — Linguagem & Conceitos Fundamentais
  { id: "alfabetizacao_inicial", label: "Alfabetização", emoji: "🔤", group: "educativo" },
  { id: "pensamento_matematico", label: "Matemática", emoji: "🔢", group: "educativo" },
  { id: "cores", label: "Cores", emoji: "🎨", group: "educativo" },
  { id: "opostos_espacial", label: "Opostos", emoji: "↕️", group: "educativo" },
  // Temas educativos — Habilidades de Vida & Rotinas Diárias
  { id: "higiene_desfralde", label: "Higiene", emoji: "🧼", group: "educativo" },
  { id: "rotina_dormir", label: "Hora de Dormir", emoji: "🌙", group: "educativo" },
  { id: "alimentacao_saudavel", label: "Alimentação", emoji: "🥗", group: "educativo" },
  { id: "vestir_autonomia", label: "Vestir-se Sozinho", emoji: "👕", group: "educativo" },
  // Temas educativos — Autoconsciência & Aprendizagem Socioemocional
  { id: "literacia_emocional", label: "Sentimentos", emoji: "💗", group: "educativo" },
  { id: "consciencia_corporal", label: "Corpo", emoji: "🙆", group: "educativo" },
  { id: "compartilhar_revezar", label: "Compartilhar", emoji: "🤝", group: "educativo" },
  // Temas educativos — Descoberta & Exploração do Mundo
  { id: "animais_sons", label: "Animais e Sons", emoji: "🐾", group: "educativo" },
  { id: "transporte_ajudantes", label: "Transporte", emoji: "🚚", group: "educativo" },
  { id: "clima_estacoes", label: "Clima e Estações", emoji: "⛅", group: "educativo" },
];

export const themeLabel = (id: string | null | undefined) =>
  THEMES.find((t) => t.id === id)?.label ?? "—";

/** Etapas finais (dependem de personagem + história). */
export const STEPS: {
  key: "ebook" | "video" | "narrated-video";
  label: string;
  cost: string;
  hint: string;
}[] = [
  {
    key: "ebook",
    label: "Montar ebook",
    cost: "1 crédito",
    hint: "E-book ilustrado (precisa de personagem aprovado + história).",
  },
  {
    key: "video",
    label: "Gerar animação",
    cost: "5 créditos",
    hint: "Clipe curto (5–10s) com movimento — não é o vídeo narrado.",
  },
  {
    key: "narrated-video",
    label: "Gerar vídeo narrado",
    cost: "8 créditos",
    hint: "História com narração (~1–2 min) a partir do storyboard.",
  },
];

export const HOW = [
  "Envie uma foto de frente (um rosto, luz boa).",
  "Aprove o personagem (rosto realista).",
  "Escolha o tema ou uma história pronta.",
  "Aprove o livro (capa e páginas).",
  "Baixe o PDF, peça o impresso ou gere o vídeo narrado.",
];
