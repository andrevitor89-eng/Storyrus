export type StudioAssets = {
  character_url: string | null;
  realistic_url: string | null;
  extra_characters: { name: string; url: string }[];
  page_images: string[];
  ebook_url: string | null;
  video_url: string | null;
  narrated_video_url: string | null;
};

export function mergeStudioAssets(prev: StudioAssets | null, next: StudioAssets): StudioAssets {
  if (!prev) return next;
  const prevPages = prev.page_images ?? [];
  const nextPages = next.page_images ?? [];
  return {
    ...next,
    page_images: nextPages.length === prevPages.length ? prevPages : nextPages,
  };
}
