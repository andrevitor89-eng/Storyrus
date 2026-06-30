export type Style = "realistic" | "cartoon" | "anime";

export interface Project {
  id: string;
  status: string;
  style: string | null;
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
  cost_credits: number;
  attempts: number;
  error: string | null;
}

export interface UploadUrl {
  asset_id: string;
  storage_key: string;
  upload_url: string;
  expires_in: number;
}
