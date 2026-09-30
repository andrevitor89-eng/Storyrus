import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { api } from "./api";
import type { Job, Project } from "./types";
import { demoIdFromSearch, getDemoExample } from "./demoExample";
import { themePreset } from "./studioPreset";
import logo from "./assets/logo.png";
import type { StudioAssets } from "./studio/assets";
import { resolveThemeName } from "./studio/constants";
import { ProgressList } from "./studio/ProgressList";
import { VoiceNarrationPanel } from "./studio/VoiceNarrationPanel";
import { EbookStepButtons, VideoStepButtons } from "./studio/StepButtons";
import { BookApprovalBlock, CharacterApprovalBlock } from "./studio/ApprovalBlocks";
import { useStudioPolling } from "./studio/useStudioPolling";
import { useStudioVoices } from "./studio/useStudioVoices";
import { useStudioSteps } from "./studio/useStudioSteps";
import { useStudioApprovals } from "./studio/useStudioApprovals";
import {
  StudioLangProvider,
  useStudioI18n,
  useStudioLangState,
} from "./studio/useStudioI18n";
import "./landing.css";
import "./studio.css";

export { ProgressList } from "./studio/ProgressList";

/* ---------------- ícones (SVG, sem emojis) ---------------- */
type IconProps = { className?: string };
const ICON_STROKE = 2.2;
const Svg = ({ className, children }: { className?: string; children: ReactNode }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={ICON_STROKE}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    {children}
  </svg>
);
const IcSun = ({ className }: IconProps) => (
  <Svg className={className}>
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" />
  </Svg>
);
const IcMoon = ({ className }: IconProps) => (
  <Svg className={className}>
    <path d="M20 15A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 11z" />
  </Svg>
);

export function Studio({ onLogout }: { onLogout?: () => void }) {
  const langState = useStudioLangState();
  return (
    <StudioLangProvider value={langState}>
      <StudioInner onLogout={onLogout} />
    </StudioLangProvider>
  );
}

function StudioInner({ onLogout }: { onLogout?: () => void }) {
  const { lang, setLang, t, langs } = useStudioI18n();
  const [credits, setCredits] = useState<number | null>(null);
  const [isGuest, setIsGuest] = useState(true);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [upgradeEmail, setUpgradeEmail] = useState("");
  const [upgradePassword, setUpgradePassword] = useState("");
  const [upgradeBusy, setUpgradeBusy] = useState(false);
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState<string>("");
  const [bookTitle, setBookTitle] = useState("");
  const [themeText, setThemeText] = useState("");
  const [temaId, setTemaId] = useState("");
  const [onlyName, setOnlyName] = useState(false);
  const [bookSize, setBookSize] = useState<"M" | "P">("M");
  const [artMode, setArtMode] = useState<"realista" | "cartoon">("realista");
  const [dedication, setDedication] = useState("");
  const [assets, setAssets] = useState<StudioAssets | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(() => Boolean(demoIdFromSearch()));
  const titlePreset = useRef<{ hero: string; title: string } | null>(null);
  const titleTouched = useRef(false);
  const presetApplied = useRef(false);
  const [mediaConsent, setMediaConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [colorTheme, setColorTheme] = useState<"light" | "dark">(() => {
    try {
      const s = localStorage.getItem("theme");
      if (s === "light" || s === "dark") return s;
    } catch {
      /* ignore */
    }
    return "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", colorTheme);
  }, [colorTheme]);

  useEffect(() => {
    if (!isDemo) return;
    const demo = getDemoExample();
    setChildName(demo.childName);
    setChildAge(demo.childAge);
    setBookTitle(demo.bookTitle);
    setThemeText(demo.themeText);
    setDedication(demo.dedication);
    setProject(demo.project);
    setAssets(demo.assets);
    setPhotoUploaded(true);
    setJobs([]);
  }, [isDemo]);

  useEffect(() => {
    if (presetApplied.current || isDemo) return;
    const q = new URLSearchParams(window.location.search);
    const tema = q.get("tema");
    const titulo = q.get("titulo");
    const historia = q.get("historia");
    const heroi = q.get("heroi");
    if (!tema && !titulo && !historia) return;
    presetApplied.current = true;
    if (tema) setTemaId(tema);
    if (q.get("tamanho") === "P" || q.get("tamanho") === "M") setBookSize(q.get("tamanho") as "M" | "P");
    if (q.get("modo") === "cartoon") setArtMode("cartoon");
    const onlyTheme = q.get("campos") === "tema" || q.get("campos") === "nome";
    if (q.get("campos") === "nome") setOnlyName(true);
    const fallback = tema ? themePreset(tema, lang) : null;
    const themeBody = historia || fallback?.theme || "";
    if (themeBody) setThemeText(themeBody);
    if (q.get("campos") === "nome" && titulo) {
      setBookTitle(titulo);
      if (heroi) titlePreset.current = { hero: heroi, title: titulo };
    }
    if (onlyTheme) return;
    const title = titulo || fallback?.title || "";
    if (title) setBookTitle(title);
    if (heroi && titulo) titlePreset.current = { hero: heroi, title: titulo };
  }, [isDemo, lang]);

  const refreshCredits = useCallback(async () => {
    try {
      setCredits((await api.credits()).credits);
    } catch {
      /* ignore */
    }
  }, []);

  const refreshMe = useCallback(async () => {
    try {
      const me = await api.me();
      setIsGuest(me.is_guest);
      setCredits(me.credits);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void refreshMe();
    void refreshCredits();
  }, [refreshMe, refreshCredits]);

  const getStoryBrief = useCallback(() => {
    const name = childName.trim();
    const title = bookTitle.trim();
    const theme = themeText.trim();
    const cm = bookSize === "P" ? "15×15 cm" : "20×20 cm";
    const look =
      artMode === "cartoon"
        ? "Estilo cartoon premium, traços desenhados, formas arredondadas, sem anime nem chibi."
        : "Estilo editorial suavemente realista: pele com luz suave, íris na fração da foto, cabelo fio a fio, sem cartoon.";
    const format = `Livro quadrado ${cm}, corte reto, página em sangria total, estrofe curta na faixa calma. ${look}`;
    if (lang === "en") {
      return (
        `Invent an original children's story. The book title must be: "${title}". ` +
        `Theme and ideas from the guardian: ${theme}. ` +
        (name ? `The hero's name is ${name}. ` : "") +
        format
      );
    }
    if (lang === "es") {
      return (
        `Inventa una historia infantil original. El título del libro debe ser: "${title}". ` +
        `Tema e ideas del responsable: ${theme}. ` +
        (name ? `El protagonista se llama ${name}. ` : "") +
        format
      );
    }
    return (
      `Invente uma história infantil original. O título do livro deve ser: "${title}". ` +
      `Tema e ideias do responsável: ${theme}. ` +
      (name ? `O protagonista se chama ${name}. ` : "") +
      format
    );
  }, [artMode, bookSize, bookTitle, childName, lang, themeText]);

  async function submitUpgrade(e: FormEvent) {
    e.preventDefault();
    setUpgradeBusy(true);
    setError(null);
    try {
      await api.upgrade(upgradeEmail.trim(), upgradePassword);
      setShowUpgrade(false);
      setUpgradeEmail("");
      setUpgradePassword("");
      await refreshMe();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUpgradeBusy(false);
    }
  }

  const {
    voices,
    customVoiceAvailable,
    selectedVoiceId,
    setSelectedVoiceId,
    voiceName,
    setVoiceName,
    voiceUploading,
    onVoiceFile,
    removeSelectedVoice,
  } = useStudioVoices({
    isDemo,
    mediaConsent,
    setError,
    consentError: t.errConsentVoice,
    defaultVoiceName: t.defaultVoiceName,
  });

  useStudioPolling({
    project,
    jobs,
    setProject,
    setJobs,
    setAssets,
    refreshCredits,
    isDemo,
  });

  const { runStep } = useStudioSteps({
    project,
    isDemo,
    selectedVoiceId,
    getStoryBrief,
    setBusy,
    setError,
    setJobs,
    refreshCredits,
  });

  const {
    approveCharacter,
    approveBook,
    requestPrint,
    characterApproved,
    bookApproved,
    printRequested,
  } = useStudioApprovals({
    project,
    isDemo,
    setBusy,
    setError,
    setProject,
  });

  async function start() {
    if (isDemo) return;
    if (onlyName) {
      if (!childName.trim() || childAge.trim() === "") {
        setError(t.errMissingFields);
        return;
      }
    } else if (!childName.trim() || !bookTitle.trim() || !themeText.trim() || childAge.trim() === "") {
      setError(t.errMissingFields);
      return;
    }
    if (!photo) {
      setError(t.errPhotoRequired);
      return;
    }
    if (!mediaConsent) {
      setError(t.errConsentPhoto);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const age = Number(childAge);
      const p = await api.createProject({
        theme: temaId || themeText.trim(),
        childName,
        dedication,
        childAge: Number.isNaN(age) ? undefined : age,
        style: artMode === "cartoon" ? "cartoon" : "realistic",
        bookSize,
      });
      setProject(p);
      setJobs([]);
      setAssets(null);
      setMediaConsent(true);
      await api.uploadPhoto(p.id, photo);
      setPhotoUploaded(true);
      await api.startStep(p.id, "avatar", {});
      const js = await api.listJobs(p.id);
      setJobs(js);
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const canMountEbook = photoUploaded && !!project?.story_text && characterApproved;
  const canMakeVideo = bookApproved;
  const locked = busy || isDemo;
  const ebookRunning = jobs.some(
    (j) => j.type === "EBOOK" && (j.status === "PENDING" || j.status === "RUNNING"),
  );

  function exitDemo() {
    const url = new URL(window.location.href);
    url.searchParams.delete("exemplo");
    const next = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, "", next);
    setIsDemo(false);
    setProject(null);
    setAssets(null);
    setPhotoUploaded(false);
    setMediaConsent(false);
    setChildName("");
    setChildAge("");
    setBookTitle("");
    setThemeText("");
    setDedication("");
    setJobs([]);
  }

  function toggleColorTheme() {
    setColorTheme((cur) => {
      const next = cur === "light" ? "dark" : "light";
      try {
        localStorage.setItem("theme", next);
      } catch {
        /* ignore */
      }
      return next;
    });
  }

  const fieldsLocked = !!project;

  return (
    <div className="kid studio-app">
      <header className="khead" role="banner">
        <div className="khead-inner">
          <a href="/" className="kbrand" aria-label="Story R Us">
            <img className="hdr-logo" src={logo} alt="Story R Us" />
          </a>
          <div className="khead-main">
            <div className="khead-top">
              <div className="khead-top-inner">
                <div className="khead-utils">
                  <div
                    className="lang"
                    role="group"
                    aria-label={t.langAria}
                    data-testid="studio-lang"
                  >
                    {langs.map((code) => (
                      <button
                        key={code}
                        type="button"
                        className={lang === code ? "on" : ""}
                        aria-pressed={lang === code}
                        onClick={() => setLang(code)}
                      >
                        {code.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="theme-toggle"
                    onClick={toggleColorTheme}
                    aria-label={t.themeToggleAria}
                  >
                    {colorTheme === "dark" ? <IcSun className="ti" /> : <IcMoon className="ti" />}
                    <span className="theme-toggle-label">
                      {colorTheme === "dark" ? t.themeToLight : t.themeToDark}
                    </span>
                  </button>
                  <span className="studio-credits-pill" data-testid="studio-credits" aria-live="polite">
                    {t.credits}: {credits ?? "…"}
                  </span>
                  {isGuest && (
                    <button
                      type="button"
                      className="kutil"
                      data-testid="studio-upgrade-open"
                      aria-expanded={showUpgrade}
                      aria-controls="studio-upgrade-form"
                      onClick={() => setShowUpgrade((v) => !v)}
                    >
                      {t.upgradeOpen}
                    </button>
                  )}
                  {onLogout && (
                    <button type="button" className="kutil link" onClick={onLogout}>
                      {t.logout}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main id="studio-main" className="studio-page" aria-busy={busy || undefined}>
        {showUpgrade && isGuest && (
          <form
            id="studio-upgrade-form"
            className="studio-card upgrade-form"
            onSubmit={submitUpgrade}
            data-testid="studio-upgrade-form"
          >
            <h2>{t.upgradeTitle}</h2>
            <p className="muted">{t.upgradeHint}</p>
            <label>
              {t.upgradeEmail}
              <input
                type="email"
                required
                autoComplete="email"
                value={upgradeEmail}
                data-testid="studio-upgrade-email"
                onChange={(e) => setUpgradeEmail(e.target.value)}
              />
            </label>
            <label>
              {t.upgradePassword}
              <input
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={upgradePassword}
                data-testid="studio-upgrade-password"
                onChange={(e) => setUpgradePassword(e.target.value)}
              />
            </label>
            <div className="studio-actions">
              <button type="submit" className="kbtn kbtn-primary" disabled={upgradeBusy} data-testid="studio-upgrade-submit">
                {upgradeBusy ? t.upgradeSaving : t.upgradeSubmit}
              </button>
              <button type="button" className="link" onClick={() => setShowUpgrade(false)}>
                {t.upgradeLater}
              </button>
            </div>
          </form>
        )}

        {isDemo && (
          <div className="demo-banner" role="status" aria-live="polite">
            <p>{t.demoBanner}</p>
            <button type="button" className="kbtn kbtn-soft" onClick={exitDemo}>
              {t.demoCta}
            </button>
          </div>
        )}

        {error && (
          <p className="studio-error" role="alert">
            {error}
          </p>
        )}

        <section className="studio-card" aria-labelledby="studio-create-heading">
          <h2 id="studio-create-heading">{t.createTitle}</h2>
          {project ? (
            <p className="studio-meta">{t.projectLocked}</p>
          ) : (
            <p className="studio-slogan">{t.slogan}</p>
          )}

          <div className="how" role="region" aria-labelledby="studio-how-heading">
            <h3 className="field-label" id="studio-how-heading">
              {t.howTitle}
            </h3>
            <ol>
              {t.how.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ol>
          </div>

          <div className="studio-grid two">
            <label className="studio-field">
              {t.childName}
              <input
                disabled={fieldsLocked}
                value={childName}
                onChange={(e) => {
                  const name = e.target.value;
                  setChildName(name);
                  const preset = titlePreset.current;
                  if (!preset || titleTouched.current) return;
                  const next = name.trim();
                  setBookTitle(next ? preset.title.split(preset.hero).join(next) : preset.title);
                }}
                placeholder={t.childNamePh}
                maxLength={80}
              />
            </label>
            <label className="studio-field">
              {t.childAge}
              <input
                disabled={fieldsLocked}
                type="number"
                inputMode="numeric"
                min={0}
                max={12}
                value={childAge}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === "") return setChildAge("");
                  const n = Math.max(0, Math.min(12, Math.floor(Number(v))));
                  setChildAge(Number.isNaN(n) ? "" : String(n));
                }}
                placeholder={t.childAgePh}
              />
            </label>
          </div>

          {onlyName ? (
            <p className="studio-meta" role="status">
              {t.chosenBook}: <b>{bookTitle || themeText}</b>
            </p>
          ) : (
            <>
              <label className="studio-field">
                {t.bookTitle}
                <input
                  disabled={fieldsLocked}
                  value={bookTitle}
                  onChange={(e) => {
                    titleTouched.current = true;
                    setBookTitle(e.target.value);
                  }}
                  placeholder={t.bookTitlePh}
                  maxLength={120}
                />
              </label>

              <label className="studio-field">
                {t.themeFree}
                <textarea
                  disabled={fieldsLocked}
                  value={themeText}
                  onChange={(e) => setThemeText(e.target.value)}
                  placeholder={t.themeFreePh}
                  maxLength={500}
                  rows={3}
                />
              </label>
              <p className="muted field-hint">{t.themeHint}</p>

              <label className="studio-field">
                {t.dedication}
                <input
                  disabled={fieldsLocked}
                  value={dedication}
                  onChange={(e) => setDedication(e.target.value)}
                  placeholder={t.dedicationPh}
                  maxLength={200}
                />
              </label>
            </>
          )}

          <div className="studio-field" role="group" aria-label={t.bookSize}>
            {t.bookSize}
            <div className="studio-actions">
              {(["M", "P"] as const).map((choice) => (
                <button
                  key={choice}
                  type="button"
                  className={bookSize === choice ? "kbtn kbtn-primary" : "kbtn kbtn-soft"}
                  aria-pressed={bookSize === choice}
                  disabled={fieldsLocked}
                  onClick={() => setBookSize(choice)}
                >
                  {choice === "M" ? t.bookSizeM : t.bookSizeP}
                </button>
              ))}
            </div>
          </div>

          {!fieldsLocked && (
            <>
              <p className="studio-field">{t.photoField}</p>
              <p className="muted field-hint">{t.photoFieldHint}</p>
              <div className="studio-upload-row" role="group" aria-label={t.ariaPhotoGroup}>
                <input
                  type="file"
                  accept="image/*"
                  disabled={isDemo}
                  data-testid="studio-photo-input"
                  aria-label={t.ariaSelectPhoto}
                  onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
                />
              </div>
              <label className="studio-consent">
                <input
                  type="checkbox"
                  checked={mediaConsent}
                  disabled={isDemo}
                  data-testid="studio-media-consent"
                  onChange={(e) => setMediaConsent(e.target.checked)}
                />
                {t.consent}
              </label>
              <div className="studio-actions">
                <button
                  type="button"
                  className="kbtn kbtn-go"
                  disabled={locked}
                  onClick={start}
                  data-testid="studio-create-project"
                >
                  {t.createProject}
                </button>
              </div>
            </>
          )}
        </section>

        {project && (
          <section
            className="studio-card"
            data-testid="studio-project"
            aria-labelledby="studio-project-heading"
            aria-busy={busy || undefined}
          >
            <h2 id="studio-project-heading">{t.projectTitle}</h2>
            <p className="studio-meta" role="status" aria-live="polite">
              {t.metaBookTitle}: <b>{bookTitle || "—"}</b> · {t.metaTheme}:{" "}
              <b>{resolveThemeName(project.theme ?? themeText, t.themes)}</b> · {t.statusLabel}:{" "}
              <b>{project.status}</b>
            </p>

            {photoUploaded && (
              <p className="muted" role="status">
                {t.photoSent}
              </p>
            )}

            <div className="studio-actions">
              <button
                type="button"
                className="kbtn kbtn-primary"
                disabled={locked || !photoUploaded}
                onClick={() => runStep("story")}
                data-testid="studio-generate-story"
              >
                {t.generateStory} <span className="muted">{t.oneCredit}</span>
              </button>
            </div>

            <VoiceNarrationPanel
              customVoiceAvailable={customVoiceAvailable}
              voiceName={voiceName}
              setVoiceName={setVoiceName}
              voiceUploading={voiceUploading}
              locked={locked}
              mediaConsent={mediaConsent}
              onVoiceFile={onVoiceFile}
              voices={voices}
              selectedVoiceId={selectedVoiceId}
              setSelectedVoiceId={setSelectedVoiceId}
              removeSelectedVoice={removeSelectedVoice}
            />

            <EbookStepButtons locked={locked} canMountEbook={canMountEbook} runStep={runStep} />
            {!characterApproved && photoUploaded && (
              <p className="muted">{t.approveCharacterFirst}</p>
            )}

            <ProgressList jobs={jobs} />

            <div className="results" role="region" aria-label={t.ariaResults}>
              {assets?.character_url && (
                <CharacterApprovalBlock
                  characterUrl={assets.character_url}
                  characterApproved={characterApproved}
                  locked={locked}
                  onApprove={approveCharacter}
                  onRegenerate={() => runStep("avatar")}
                />
              )}

              {project.story_text && (
                <div
                  className="result-block"
                  data-testid="studio-story-result"
                  role="region"
                  aria-labelledby="studio-story-result-heading"
                >
                  <h3 className="field-label" id="studio-story-result-heading">
                    {t.storyTitle}
                  </h3>
                  <pre
                    className="story"
                    style={{ whiteSpace: "pre-wrap" }}
                    data-testid="studio-story-text"
                  >
                    {project.story_text}
                  </pre>
                </div>
              )}

              {(assets?.ebook_url || (assets?.page_images?.length ?? 0) > 0 || ebookRunning) && (
                <BookApprovalBlock
                  pageImages={assets?.page_images ?? []}
                  ebookUrl={assets?.ebook_url ?? null}
                  bookApproved={bookApproved}
                  locked={locked}
                  canMountEbook={canMountEbook}
                  printRequested={printRequested}
                  onApprove={approveBook}
                  onRegenerate={() => runStep("ebook")}
                  onRequestPrint={requestPrint}
                />
              )}

              {bookApproved && (
                <div className="result-block" role="region" aria-labelledby="studio-video-heading">
                  <h3 className="field-label" id="studio-video-heading">
                    {t.videoTitle}
                  </h3>
                  <p className="muted">{t.videoHint}</p>
                  <VideoStepButtons locked={locked} canMakeVideo={canMakeVideo} runStep={runStep} />
                </div>
              )}

              {assets?.video_url && (
                <div
                  className="result-block"
                  role="region"
                  aria-labelledby="studio-animation-heading"
                >
                  <h3 className="field-label" id="studio-animation-heading">
                    {t.animationTitle}
                  </h3>
                  {assets.video_url.toLowerCase().includes(".gif") ? (
                    <img
                      src={assets.video_url}
                      alt={t.animationTitle}
                      style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                    />
                  ) : (
                    <video
                      src={assets.video_url}
                      controls
                      aria-label={t.ariaAnimationGenerated}
                      style={{ maxWidth: 360, width: "100%" }}
                    />
                  )}
                </div>
              )}

              {assets?.narrated_video_url && (
                <div
                  className="result-block"
                  role="region"
                  aria-labelledby="studio-narrated-heading"
                >
                  <h3 className="field-label" id="studio-narrated-heading">
                    {t.narratedTitle}
                  </h3>
                  {assets.narrated_video_url.toLowerCase().includes(".gif") ? (
                    <img
                      src={assets.narrated_video_url}
                      alt={t.narratedTitle}
                      style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                    />
                  ) : (
                    <video
                      src={assets.narrated_video_url}
                      controls
                      aria-label={t.ariaNarratedGenerated}
                      style={{ maxWidth: 360, width: "100%" }}
                    />
                  )}
                </div>
              )}
            </div>

            <button
              type="button"
              className="link"
              onClick={() => (isDemo ? exitDemo() : setProject(null))}
            >
              {isDemo ? t.createMyStory : t.newProject}
            </button>
          </section>
        )}
      </main>
    </div>
  );
}
