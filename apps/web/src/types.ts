export type Style = "cgi_3d" | "realistic" | "cartoon" | "anime";

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

// História pronta do catálogo (template traduzido, personalizado com o nome).
export interface StoryTemplate {
  id: string;
  titulo: string;
  genero: string;
  idade: string;
  tematica: string;
  emoji: string;
  paginas: number;
}

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
  narrated_video_url?: string | null;
  character_approved_at?: string | null;
  book_approved_at?: string | null;
  print_requested_at?: string | null;
  print_status?: string | null;
  created_at: string;
}

export interface Job {
  id: string;
  project_id: string;
  type: "AVATAR" | "STORY" | "EBOOK" | "STORYBOARD" | "VIDEO" | "NARRATED_VIDEO" | "REALISTIC" | "EXTRA_CHARACTER";
  status: "PENDING" | "RUNNING" | "DONE" | "FAILED";
  provider: string | null;
  cost_credits: number;
  cost_usd?: number | null;
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

export interface UsageBucket {
  key: string;
  usd: number;
  jobs: number;
}

export interface UsageBook {
  project_id: string;
  child_name: string | null;
  status: string;
  usd: number | null;
  unmeasured_jobs: number;
  updated_at: string;
}

export interface UsageJob {
  id: string;
  project_id: string;
  child_name: string | null;
  type: string;
  status: string;
  provider: string | null;
  cost_usd: number | null;
  attempts: number;
  created_at: string;
}

export interface UsageReport {
  timezone: string;
  from_at: string;
  to_at: string;
  today_usd: number;
  month_usd: number;
  range_usd: number;
  books_count: number;
  avg_book_usd: number | null;
  by_type: UsageBucket[];
  by_provider: UsageBucket[];
  books: UsageBook[];
  recent_jobs: UsageJob[];
}

export interface UploadUrl {
  asset_id: string;
  storage_key: string;
  upload_url: string;
  expires_in: number;
}

export interface UserVoice {
  id: string;
  name: string;
  is_default: boolean;
  mime_type: string;
  created_at: string;
}

export interface VoiceList {
  items: UserVoice[];
  custom_voice_available: boolean;
}
