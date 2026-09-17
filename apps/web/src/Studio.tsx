import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "./api";
import type { ExtraCharacter, Job, Project, StoryTemplate, Theme } from "./types";
import { demoIdFromSearch, getDemoExample } from "./demoExample";
import logo from "./assets/logo.png";
import type { StudioAssets } from "./studio/assets";
import { THEMES, resolveThemeName } from "./studio/constants";
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

export { ProgressList } from "./studio/ProgressList";

type StoryMode = "invent" | "write" | "file" | "catalog";

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
  const [selectedThemes, setSelectedThemes] = useState<Theme[]>(["adventure"]);
  const theme = selectedThemes[0] ?? "adventure";
  const extraTheme = selectedThemes[1];
  function toggleTheme(id: Theme) {
    setSelectedThemes((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  }
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [extraChars, setExtraChars] = useState<ExtraCharacter[]>([]);
  const [extraCharFile, setExtraCharFile] = useState<File | null>(null);
  const [extraCharName, setExtraCharName] = useState("");
  const [storyMode, setStoryMode] = useState<StoryMode>("invent");
  const [storyText, setStoryText] = useState("");
  const [templates, setTemplates] = useState<StoryTemplate[] | null>(null);
  const [appliedTemplate, setAppliedTemplate] = useState<string | null>(null);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState<string>("");
  const [dedication, setDedication] = useState("");
  const [assets, setAssets] = useState<StudioAssets | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(() => Boolean(demoIdFromSearch()));
  const [mediaConsent, setMediaConsent] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    try {
      const s = localStorage.getItem("theme");
      document.documentElement.setAttribute("data-theme", s === "light" ? "light" : "dark");
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (demoIdFromSearch()) return;
    const q = new URLSearchParams(window.location.search).get("tema");
    if (q && THEMES.some((x) => x.id === q)) setSelectedThemes([q as Theme]);
  }, []);

  useEffect(() => {
    if (demoIdFromSearch()) return;
    const h = new URLSearchParams(window.location.search).get("historia");
    if (!h) return;
    setStoryMode("catalog");
    api.storyTemplates().then(setTemplates).catch((e) => setError((e as Error).message));
  }, []);

  useEffect(() => {
    if (!isDemo) return;
    const demo = getDemoExample();
    setSelectedThemes(demo.themes);
    setChildName(demo.childName);
    setChildAge(demo.childAge);
    setDedication(demo.dedication);
    setStoryText(demo.project.story_text ?? "");
    setProject(demo.project);
    setAssets(demo.assets);
    setPhotoUploaded(true);
    setJobs([]);
  }, [isDemo]);

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
  }, [refreshMe]);

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
    setBusy(true);
    setError(null);
    try {
      const age = childAge.trim() === "" ? undefined : Number(childAge);
      const p = await api.createProject(theme, extraTheme, childName, dedication, age);
      setProject(p);
      setJobs([]);
      setPhotoUploaded(false);
      setAssets(null);
      setStoryText("");
      setMediaConsent(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function upload() {
    if (!project || !photo || isDemo) return;
    if (!mediaConsent) {
      setError(t.errConsentPhoto);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.uploadPhoto(project.id, photo);
      setPhotoUploaded(true);
      await api.startStep(project.id, "avatar", {});
      const js = await api.listJobs(project.id);
      setJobs(js);
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function saveStory() {
    if (!project || !storyText.trim() || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const p = await api.setStoryText(project.id, storyText);
      setProject(p);
      const js = await api.listJobs(project.id);
      setJobs(js);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function openCatalog() {
    setStoryMode("catalog");
    if (templates) return;
    try {
      setTemplates(await api.storyTemplates());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function applyTemplate(templateId: string) {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const p = await api.applyStoryTemplate(project.id, templateId);
      setProject(p);
      setAppliedTemplate(templateId);
      const js = await api.listJobs(project.id);
      setJobs(js);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onStoryFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const { text } = await api.extractStory(project.id, file);
      setStoryText(text);
      setStoryMode("write");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function uploadExtraCharacter() {
    if (!project || !extraCharFile || isDemo) return;
    if (!mediaConsent) {
      setError(t.errConsentExtra);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.uploadExtraCharacter(project.id, extraCharFile, extraCharName);
      const p = await api.getProject(project.id);
      setProject(p);
      setExtraChars(p.extra_characters || []);
      setExtraCharFile(null);
      setExtraCharName("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function generateExtraCharacters() {
    if (!project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      await api.startStep(project.id, "extra-character", {});
      const js = await api.listJobs(project.id);
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
    setDedication("");
    setStoryText("");
    setJobs([]);
    setAppliedTemplate(null);
  }

  function themeChipLabel(id: Theme) {
    return t.themes[id];
  }

  return (
    <div className="studio">
      <header role="banner">
        <img className="hdr-logo" src={logo} alt="Story R Us" />
        <strong>Story R Us</strong>
        <span className="spacer" />
        <div className="studio-lang" role="group" aria-label={t.langAria} data-testid="studio-lang">
          {langs.map((code) => (
            <button
              key={code}
              type="button"
              className={`chip ${lang === code ? "on" : ""}`}
              aria-pressed={lang === code}
              onClick={() => setLang(code)}
            >
              {code.toUpperCase()}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="chip"
          onClick={() => {
            const cur =
              document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", cur);
            try {
              localStorage.setItem("theme", cur);
            } catch {
              /* ignore */
            }
          }}
          aria-label={t.themeToggleAria}
        >
          {t.theme}
        </button>
        <span className="credits" data-testid="studio-credits" aria-live="polite">
          {t.credits}: {credits ?? "…"}
        </span>
        {isGuest && (
          <button
            type="button"
            className="chip"
            data-testid="studio-upgrade-open"
            aria-expanded={showUpgrade}
            aria-controls="studio-upgrade-form"
            onClick={() => setShowUpgrade((v) => !v)}
          >
            {t.upgradeOpen}
          </button>
        )}
        {onLogout && (
          <button type="button" className="link" onClick={onLogout}>
            {t.logout}
          </button>
        )}
      </header>

      <main id="studio-main" aria-busy={busy || undefined}>
        {showUpgrade && isGuest && (
          <form
            id="studio-upgrade-form"
            className="card upgrade-form"
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
            <div className="upload">
              <button type="submit" disabled={upgradeBusy} data-testid="studio-upgrade-submit">
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
            <button type="button" onClick={exitDemo}>
              {t.demoCta}
            </button>
          </div>
        )}

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        <section className="card" aria-labelledby="studio-create-heading">
          <h2 id="studio-create-heading">{t.createTitle}</h2>
          {project ? (
            <p className="muted">{t.projectLocked}</p>
          ) : (
            <p className="slogan">{t.slogan}</p>
          )}

          <h3 className="field-label" id="studio-themes-aventura">
            {t.pickThemes}
          </h3>
          <p className="muted">{t.pickThemesHint}</p>
          <div className="styles" role="group" aria-labelledby="studio-themes-aventura">
            {THEMES.filter((x) => x.group === "aventura").map((x) => {
              const order = selectedThemes.indexOf(x.id);
              return (
                <button
                  key={x.id}
                  type="button"
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  aria-pressed={order >= 0}
                  onClick={() => toggleTheme(x.id)}
                >
                  {x.emoji} {themeChipLabel(x.id)}
                  {order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label" id="studio-themes-datas">
            {t.groupDatas}
          </h3>
          <div className="styles" role="group" aria-labelledby="studio-themes-datas">
            {THEMES.filter((x) => x.group === "datas").map((x) => {
              const order = selectedThemes.indexOf(x.id);
              return (
                <button
                  key={x.id}
                  type="button"
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  aria-pressed={order >= 0}
                  onClick={() => toggleTheme(x.id)}
                >
                  {x.emoji} {themeChipLabel(x.id)}
                  {order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label" id="studio-themes-educativo">
            {t.groupEducativo}
          </h3>
          <div className="styles" role="group" aria-labelledby="studio-themes-educativo">
            {THEMES.filter((x) => x.group === "educativo").map((x) => {
              const order = selectedThemes.indexOf(x.id);
              return (
                <button
                  key={x.id}
                  type="button"
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  aria-pressed={order >= 0}
                  onClick={() => toggleTheme(x.id)}
                >
                  {x.emoji} {themeChipLabel(x.id)}
                  {order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">{t.nameAgeDedication}</h3>
          <label>
            {t.childName}
            <input
              disabled={!!project}
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder={t.childNamePh}
              maxLength={80}
            />
          </label>
          <label>
            {t.childAge}
            <input
              disabled={!!project}
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
          <label>
            {t.dedication}
            <input
              disabled={!!project}
              value={dedication}
              onChange={(e) => setDedication(e.target.value)}
              placeholder={t.dedicationPh}
              maxLength={200}
            />
          </label>

          {!project && (
            <button type="button" disabled={locked} onClick={start} data-testid="studio-create-project">
              {t.createProject}
            </button>
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
        </section>

        {project && (
          <section
            className="card"
            data-testid="studio-project"
            aria-labelledby="studio-project-heading"
            aria-busy={busy || undefined}
          >
            <h2 id="studio-project-heading">{t.projectTitle}</h2>
            <p className="muted" role="status" aria-live="polite">
              {t.metaTheme}: <b>{resolveThemeName(project.theme ?? theme, t.themes)}</b>
              {(project.extra_theme ?? extraTheme) && (
                <>
                  {" "}
                  + <b>{resolveThemeName(project.extra_theme ?? extraTheme, t.themes)}</b>
                </>
              )}{" "}
              · {t.styleLabel}: <b>{t.artStyleRealistic}</b> · {t.statusLabel}:{" "}
              <b>{project.status}</b>
            </p>

            <label className="consent">
              <input
                type="checkbox"
                checked={mediaConsent}
                disabled={isDemo}
                data-testid="studio-media-consent"
                onChange={(e) => setMediaConsent(e.target.checked)}
              />
              {t.consent}
            </label>

            <div className="upload" role="group" aria-label={t.ariaPhotoGroup}>
              <input
                type="file"
                accept="image/*"
                disabled={isDemo}
                data-testid="studio-photo-input"
                aria-label={t.ariaSelectPhoto}
                onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
              />
              <button
                type="button"
                disabled={!photo || locked || !mediaConsent}
                onClick={upload}
                data-testid="studio-upload-photo"
              >
                {photoUploaded ? t.photoSent : t.sendPhoto}
              </button>
            </div>
            <p className="muted" style={{ marginTop: 6 }}>
              {t.photoHint}
            </p>

            <h3 className="field-label" id="studio-extra-chars-heading">
              {t.extraCharsTitle}
            </h3>
            <div className="upload" role="group" aria-labelledby="studio-extra-chars-heading">
              <input
                type="file"
                accept="image/*"
                aria-label={t.ariaSelectExtraPhoto}
                onChange={(e) => setExtraCharFile(e.target.files?.[0] ?? null)}
              />
              <input
                value={extraCharName}
                onChange={(e) => setExtraCharName(e.target.value)}
                placeholder={t.extraCharNamePh}
                aria-label={t.ariaExtraCharName}
                maxLength={40}
                style={{ flex: 1, minWidth: 120 }}
              />
              <button
                type="button"
                disabled={!extraCharFile || locked || !mediaConsent}
                onClick={uploadExtraCharacter}
              >
                {t.add}
              </button>
            </div>
            {extraChars.length > 0 && (
              <div style={{ margin: "8px 0" }} role="status" aria-live="polite">
                <p className="muted">{t.extrasAdded(extraChars.length)}</p>
                <button type="button" disabled={locked} onClick={generateExtraCharacters}>
                  {t.generateExtras} <span className="muted">{t.creditEach}</span>
                </button>
              </div>
            )}

            <h3 className="field-label" id="studio-story-mode-heading">
              {t.storyTitle}
            </h3>
            <div className="styles" role="tablist" aria-labelledby="studio-story-mode-heading">
              <button
                type="button"
                role="tab"
                id="studio-story-tab-invent"
                aria-selected={storyMode === "invent"}
                aria-controls="studio-story-panel"
                className={`chip ${storyMode === "invent" ? "on" : ""}`}
                onClick={() => setStoryMode("invent")}
              >
                {t.inventAi}
              </button>
              <button
                type="button"
                role="tab"
                id="studio-story-tab-write"
                aria-selected={storyMode === "write"}
                aria-controls="studio-story-panel"
                className={`chip ${storyMode === "write" ? "on" : ""}`}
                onClick={() => setStoryMode("write")}
              >
                {t.writeMine}
              </button>
              <button
                type="button"
                role="tab"
                id="studio-story-tab-file"
                aria-selected={storyMode === "file"}
                aria-controls="studio-story-panel"
                className={`chip ${storyMode === "file" ? "on" : ""}`}
                onClick={() => setStoryMode("file")}
              >
                {t.sendFile}
              </button>
              <button
                type="button"
                role="tab"
                id="studio-story-tab-catalog"
                aria-selected={storyMode === "catalog"}
                aria-controls="studio-story-panel"
                className={`chip ${storyMode === "catalog" ? "on" : ""}`}
                onClick={openCatalog}
              >
                {t.readyStories}
              </button>
            </div>

            <div
              id="studio-story-panel"
              role="tabpanel"
              aria-labelledby={`studio-story-tab-${storyMode}`}
            >
              {storyMode === "invent" && (
                <button
                  type="button"
                  disabled={locked}
                  onClick={() => runStep("story")}
                  data-testid="studio-generate-story"
                >
                  {t.generateStory} <span className="muted">{t.oneCredit}</span>
                </button>
              )}

              {storyMode === "catalog" && (
                <div className="story-catalog" role="list" aria-label={t.ariaCatalog}>
                  {!templates && (
                    <p className="muted" role="status" aria-live="polite">
                      {t.loadingCatalog}
                    </p>
                  )}
                  {templates && !project?.child_name && (
                    <p className="muted">{t.needChildName}</p>
                  )}
                  {templates?.map((tpl) => (
                    <div
                      key={tpl.id}
                      className="catalog-item"
                      role="listitem"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        padding: "8px 0",
                        borderBottom: "1px solid var(--border, #333)",
                      }}
                    >
                      <span style={{ fontSize: 22 }} aria-hidden="true">
                        {tpl.emoji}
                      </span>
                      <div style={{ flex: 1 }}>
                        <strong>
                          {tpl.titulo.replace("{NOME}", project?.child_name || "{nome}")}
                        </strong>
                        <div className="muted" style={{ fontSize: 12 }}>
                          {t.catalogMeta(tpl.tematica, tpl.idade, tpl.paginas, tpl.genero)}
                        </div>
                      </div>
                      <button
                        type="button"
                        disabled={locked || !project}
                        aria-pressed={appliedTemplate === tpl.id}
                        onClick={() => applyTemplate(tpl.id)}
                      >
                        {appliedTemplate === tpl.id ? t.applied : t.use}
                        {appliedTemplate !== tpl.id && <span className="muted">{t.free}</span>}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {storyMode === "file" && (
                <div className="upload">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    aria-label={t.ariaStoryFile}
                    onChange={onStoryFile}
                  />
                  <span className="muted">{t.fileHint}</span>
                </div>
              )}

              {(storyMode === "write" || storyMode === "file") && (
                <div className="story-write">
                  <textarea
                    className="story-input"
                    rows={8}
                    style={{ width: "100%", boxSizing: "border-box", resize: "vertical" }}
                    placeholder={t.storyPlaceholder}
                    aria-label={t.ariaStoryText}
                    value={storyText}
                    onChange={(e) => setStoryText(e.target.value)}
                  />
                  <button
                    type="button"
                    disabled={locked || !storyText.trim()}
                    onClick={saveStory}
                  >
                    {t.saveStory}
                  </button>
                </div>
              )}
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

              {assets?.extra_characters && assets.extra_characters.length > 0 && (
                <div
                  className="result-block"
                  role="region"
                  aria-labelledby="studio-extra-results-heading"
                >
                  <h3 className="field-label" id="studio-extra-results-heading">
                    {t.extrasResult}
                  </h3>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }} role="list">
                    {assets.extra_characters.map((ec, i) => (
                      <div key={i} style={{ textAlign: "center" }} role="listitem">
                        <img
                          src={ec.url}
                          alt={ec.name}
                          style={{ width: 100, height: 100, objectFit: "cover", borderRadius: 50 }}
                        />
                        <p className="muted" style={{ margin: "4px 0 0" }}>
                          {ec.name}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
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
