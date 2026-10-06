import { useEffect } from "react";
import { OWNER_PAGES, type OwnerPage } from "./ownerPages";

export { OWNER_PAGES, applyOwnerPageMeta } from "./ownerPages";
export type { OwnerPage } from "./ownerPages";

export function useOwnerPageTitle(path: OwnerPage["path"]) {
  const page = OWNER_PAGES.find((item) => item.path === path);
  const title = page?.title;
  const description = page?.description;
  useEffect(() => {
    if (!title || !description) return;
    const previousTitle = document.title;
    const desc = document.querySelector('meta[name="description"]');
    const ogTitle = document.querySelector('meta[property="og:title"]');
    const ogDesc = document.querySelector('meta[property="og:description"]');
    const previousDesc = desc?.getAttribute("content");
    const previousOgTitle = ogTitle?.getAttribute("content");
    const previousOgDesc = ogDesc?.getAttribute("content");
    document.title = title;
    desc?.setAttribute("content", description);
    ogTitle?.setAttribute("content", title);
    ogDesc?.setAttribute("content", description);
    return () => {
      document.title = previousTitle;
      if (previousDesc != null) desc?.setAttribute("content", previousDesc);
      if (previousOgTitle != null) ogTitle?.setAttribute("content", previousOgTitle);
      if (previousOgDesc != null) ogDesc?.setAttribute("content", previousOgDesc);
    };
  }, [title, description]);
}
