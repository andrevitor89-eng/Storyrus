import { useSyncExternalStore, type ImgHTMLAttributes } from "react";
import logoDark from "./assets/logo.png";
import logoLight from "./assets/logo-light.png";

function readTheme(): "light" | "dark" {
  if (typeof document !== "undefined") {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr === "light" || attr === "dark") return attr;
  }
  try {
    const s = localStorage.getItem("theme");
    if (s === "light" || s === "dark") return s;
  } catch {
    /* ignore */
  }
  return "dark";
}

function subscribeTheme(onStoreChange: () => void): () => void {
  const el = document.documentElement;
  const obs = new MutationObserver(onStoreChange);
  obs.observe(el, { attributes: true, attributeFilter: ["data-theme"] });
  window.addEventListener("storage", onStoreChange);
  return () => {
    obs.disconnect();
    window.removeEventListener("storage", onStoreChange);
  };
}

function useDocumentTheme(enabled: boolean): "light" | "dark" {
  return useSyncExternalStore(
    enabled ? subscribeTheme : () => () => {},
    readTheme,
    () => "dark",
  );
}

type BrandLogoProps = {
  className?: string;
  alt?: string;
  /** When the parent already owns theme state, pass it to avoid a second source of truth. */
  theme?: "light" | "dark";
  "data-testid"?: string;
} & Omit<ImgHTMLAttributes<HTMLImageElement>, "src" | "alt" | "className">;

export function BrandLogo({
  className,
  alt = "Story R Us",
  theme: themeProp,
  "data-testid": testId,
  ...rest
}: BrandLogoProps) {
  const docTheme = useDocumentTheme(themeProp == null);
  const theme = themeProp ?? docTheme;
  return (
    <img
      className={className}
      src={theme === "light" ? logoLight : logoDark}
      alt={alt}
      data-testid={testId}
      {...rest}
    />
  );
}
