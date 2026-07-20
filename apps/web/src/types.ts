export type Style = "realistic" | "cartoon" | "anime";

export type Theme =
  | "adventure"
  | "princess"
  | "superhero"
  | "space"
  | "underwater"
  | "dinosaurs"
  | "fantasy"
  | "birthday"
  | "christmas"
  | "easter"
  | "childrens_day"
  | "mothers_day"
  | "fathers_day"
  | "new_year"
  // Temas educativos (Linguagem & Conceitos Fundamentais)
  | "alfabetizacao_inicial"
  | "pensamento_matematico"
  | "cores"
  | "opostos_espacial"
  // Temas educativos (Habilidades de Vida & Rotinas Diárias)
  | "higiene_desfralde"
  | "rotina_dormir"
  | "alimentacao_saudavel"
  | "vestir_autonomia"
  // Temas educativos (Autoconsciência & Aprendizagem Socioemocional)
  | "literacia_emocional"
  | "consciencia_corporal"
  | "compartilhar_revezar"
  // Temas educativos (Descoberta & Exploração do Mundo)
  | "animais_sons"
  | "transporte_ajudantes"
  | "clima_estacoes";

export interface ExtraCharacter {
  name: string;
  storage_key: string;
  mime: string;
  character_storage_key?: string;
  character_mime?: string;
}

export interface Project {
  id: string;
  status: string;
  style: string | null;
  theme?: string | null;
  extra_theme?: string | null;
  child_name?: string | null;
  child_age?: number | null;
  dedication?: string | null;
  language?: string | null;
  extra_characters?: ExtraCharacter[];
  story_text: string | null;
  ebook_url: string | null;
  video_url: string | null;
  created_at: string;
}

export interface Job {
  id: string;
  project_id: string;
  type: "AVATAR" | "STORY" | "EBOOK" | "STORYBOARD" | "VIDEO";
  status: "PENDING" | "RUNNING" | "DONE" | "FAILED";
  provider: string | null;
  cost_credits: number;
  attempts: number;
  error: string | null;
  created_at: string;
}

export interface JobAccepted {
  job_id: string;
  status: string;
  type: Job["type"];
  estimated_cost_credits: number;
}

export interface UploadUrl {
  asset_id: string;
  storage_key: string;
  upload_url: string;
  expires_in: number;
}
