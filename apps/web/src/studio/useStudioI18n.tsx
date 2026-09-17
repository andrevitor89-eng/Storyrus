import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  applyDocumentLang,
  LANGS,
  type Lang,
  readStoredLang,
  writeStoredLang,
} from "../i18n/lang";
import { studioCopy, type StudioCopy } from "./i18n";

type StudioLangValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: StudioCopy;
  langs: Lang[];
};

const StudioLangContext = createContext<StudioLangValue | null>(null);

export function useStudioLangState(): StudioLangValue {
  const [lang, setLangState] = useState<Lang>(() => readStoredLang("pt"));
  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    writeStoredLang(next);
    applyDocumentLang(next);
  }, []);

  useEffect(() => {
    applyDocumentLang(lang);
    writeStoredLang(lang);
  }, [lang]);

  const t = useMemo(() => studioCopy(lang), [lang]);
  return { lang, setLang, t, langs: LANGS };
}

export function StudioLangProvider({
  value,
  children,
}: {
  value: StudioLangValue;
  children: React.ReactNode;
}) {
  return <StudioLangContext.Provider value={value}>{children}</StudioLangContext.Provider>;
}

export function useStudioI18n(): StudioLangValue {
  const ctx = useContext(StudioLangContext);
  if (!ctx) {
    // Safe fallback for isolated unit tests (e.g. ProgressList alone).
    const lang = readStoredLang("pt");
    return {
      lang,
      setLang: () => undefined,
      t: studioCopy(lang),
      langs: LANGS,
    };
  }
  return ctx;
}
