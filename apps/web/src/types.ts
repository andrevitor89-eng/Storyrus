export type Style = "realistic" | "cartoon" | "anime";

export type Theme =
  | "adventure"
  | "princess"
  | "superhero"
  | "space"
  | "underwater"
  | "dinosaurs"
  | "fantasy";

export interface Project {
  id: string;
  status: string;
  style: string | null;
  theme?: string | null;
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
