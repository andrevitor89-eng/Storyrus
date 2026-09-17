import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { ExtraCharacter, Job, Project, StoryTemplate, Theme } from "./types";
import { demoIdFromSearch, getDemoExample } from "./demoExample";
import logo from "./assets/logo.png";
import type { StudioAssets } from "./studio/assets";
import {
  ART_STYLE_LABEL,
  HOW,
  THEMES,
  themeLabel,
} from "./studio/constants";
import { ProgressList } from "./studio/ProgressList";
import { VoiceNarrationPanel } from "./studio/VoiceNarrationPanel";
import { EbookStepButtons, VideoStepButtons } from "./studio/StepButtons";
import { BookApprovalBlock, CharacterApprovalBlock } from "./studio/ApprovalBlocks";
import { useStudioPolling } from "./studio/useStudioPolling";
import { useStudioVoices } from "./studio/useStudioVoices";
import { useStudioSteps } from "./studio/useStudioSteps";
import { useStudioApprovals } from "./studio/useStudioApprovals";

export { ProgressList } from "./studio/ProgressList";

type StoryMode = "invent" | "write" | "file" | "catalog";

export function Studio({ onLogout }: { onLogout?: () => void }) {
  const [credits, setCredits] = useState<number | null>(null);
  // Até 2 temas combinados na mesma história: o 1º é o principal (define
  // vilão/cenário/arco), o 2º só soma um objetivo de aprendizado extra.
  const [selectedThemes, setSelectedThemes] = useState<Theme[]>(["adventure"]);
  const theme = selectedThemes[0] ?? "adventure";
  const extraTheme = selectedThemes[1];
  function toggleTheme(id: Theme) {
    setSelectedThemes((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id]; // troca o mais antigo pelo novo
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
  // Catálogo de histórias prontas (carregado ao abrir o modo "catalog").
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

  // aplica o tema (claro/escuro) salvo na landing
  useEffect(() => {
    try {
      const s = localStorage.getItem("theme");
      document.documentElement.setAttribute("data-theme", s === "light" ? "light" : "dark");
    } catch { /* ignore */ }
  }, []);

  // pré-seleciona o tema da história vindo do catálogo (/app?tema=...)
  useEffect(() => {
    if (demoIdFromSearch()) return;
    const q = new URLSearchParams(window.location.search).get("tema");
    if (q && THEMES.some((x) => x.id === q)) setSelectedThemes([q as Theme]);
  }, []);

  // Abre histórias prontas quando a landing manda /app?historia=alfabeto_amazonia
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

  useEffect(() => {
    refreshCredits();
  }, [refreshCredits]);

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
  } = useStudioVoices({ isDemo, mediaConsent, setError });

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
      setError("Marque o consentimento para enviar a foto.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.uploadPhoto(project.id, photo);
      setPhotoUploaded(true);
      // Gera o personagem automaticamente assim que a foto chega.
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

  // Salva a história escrita/colada pelo usuário (sem IA).
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

  // Abre o catálogo de histórias prontas (carrega uma vez).
  async function openCatalog() {
    setStoryMode("catalog");
    if (templates) return;
    try {
      setTemplates(await api.storyTemplates());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  // Aplica uma história pronta do catálogo (sem IA, sem créditos).
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

  // Extrai o texto de um arquivo enviado e mostra para o usuário revisar.
  async function onStoryFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !project || isDemo) return;
    setBusy(true);
    setError(null);
    try {
      const { text } = await api.extractStory(project.id, file);
      setStoryText(text);
      setStoryMode("write"); // mostra o texto extraído para revisar antes de salvar
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Upload de personagem extra
  async function uploadExtraCharacter() {
    if (!project || !extraCharFile || isDemo) return;
    if (!mediaConsent) {
      setError("Marque o consentimento para enviar a foto do personagem extra.");
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

  // Gera os personagens ilustrados para os extras
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

  return (
    <div className="studio">
      <header>
        <img className="hdr-logo" src={logo} alt="Story R Us" />
        <strong>Story R Us</strong>
        <span className="spacer" />
        <button
          className="chip"
          onClick={() => {
            const cur = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", cur);
            try { localStorage.setItem("theme", cur); } catch { /* ignore */ }
          }}
          aria-label="Alternar tema claro/escuro"
        >
          Tema
        </button>
        <span className="credits" data-testid="studio-credits">Créditos: {credits ?? "…"}</span>
        {onLogout && (
          <button className="link" onClick={onLogout}>
            Sair
          </button>
        )}
      </header>

      {isDemo && (
        <div className="demo-banner" role="status">
          <p>Você está vendo um exemplo pronto.</p>
          <button type="button" onClick={exitDemo}>Criar a minha história</button>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>Crie a sua história</h2>
        {project ? (
          <p className="muted">
            ✓ Projeto criado — os campos abaixo ficam travados até você começar um novo projeto.
          </p>
        ) : (
          <p className="slogan">Toda história merece um protagonista — e o protagonista é você.</p>
        )}

          <h3 className="field-label">1 · Escolha até 2 temas para a aventura</h3>
          <p className="muted">
            O 1º escolhido é o tema principal (define vilão, cenário e arco); o 2º só soma
            um aprendizado extra na mesma jornada.
          </p>
          <div className="styles">
            {THEMES.filter((t) => t.group === "aventura").map((t) => {
              const order = selectedThemes.indexOf(t.id);
              return (
                <button
                  key={t.id}
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  onClick={() => toggleTheme(t.id)}
                >
                  {t.emoji} {t.label}{order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">Datas comemorativas</h3>
          <div className="styles">
            {THEMES.filter((t) => t.group === "datas").map((t) => {
              const order = selectedThemes.indexOf(t.id);
              return (
                <button
                  key={t.id}
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  onClick={() => toggleTheme(t.id)}
                >
                  {t.emoji} {t.label}{order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">Temas educativos</h3>
          <div className="styles">
            {THEMES.filter((t) => t.group === "educativo").map((t) => {
              const order = selectedThemes.indexOf(t.id);
              return (
                <button
                  key={t.id}
                  disabled={!!project}
                  className={`chip ${order >= 0 ? "on" : ""}`}
                  onClick={() => toggleTheme(t.id)}
                >
                  {t.emoji} {t.label}{order >= 0 ? ` · ${order + 1}` : ""}
                </button>
              );
            })}
          </div>

          <h3 className="field-label">2 · Nome, idade e dedicatória</h3>
          <label>
            Nome da criança
            <input
              disabled={!!project}
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder="Ex.: Lila"
              maxLength={80}
            />
          </label>
          <label>
            Idade da criança (a história é adaptada ao tom e vocabulário da idade)
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
              placeholder="Ex.: 5"
            />
          </label>
          <label>
            Dedicatória (aparece na 2ª página do livro)
            <input
              disabled={!!project}
              value={dedication}
              onChange={(e) => setDedication(e.target.value)}
              placeholder="Ex.: Para a Lila, com todo o amor da mamãe."
              maxLength={200}
            />
          </label>

          {!project && (
            <button disabled={locked} onClick={start} data-testid="studio-create-project">
              Criar projeto
            </button>
          )}

          <div className="how">
            <h3 className="field-label">Como funciona</h3>
            <ol>
              {HOW.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ol>
          </div>
      </section>

      {project && (
        <section className="card" data-testid="studio-project">
          <h2>Projeto</h2>
          <p className="muted">
            Tema: <b>{themeLabel(project.theme ?? theme)}</b>
            {(project.extra_theme ?? extraTheme) && (
              <> + <b>{themeLabel(project.extra_theme ?? extraTheme)}</b></>
            )} · Estilo: <b>{ART_STYLE_LABEL[project.style ?? "cgi_3d"] ?? "Rosto realista"}</b> ·
            Status: <b>{project.status}</b>
          </p>

          <label className="consent">
            <input
              type="checkbox"
              checked={mediaConsent}
              disabled={isDemo}
              data-testid="studio-media-consent"
              onChange={(e) => setMediaConsent(e.target.checked)}
            />
            Sou o responsável legal e autorizo o uso desta foto (e da voz, se clonar) só para criar este livro. Não usamos para divulgação.
          </label>

          <div className="upload">
            <input
              type="file"
              accept="image/*"
              disabled={isDemo}
              data-testid="studio-photo-input"
              onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
            />
            <button
              disabled={!photo || locked || !mediaConsent}
              onClick={upload}
              data-testid="studio-upload-photo"
            >
              {photoUploaded ? "Foto enviada ✓" : "Enviar foto"}
            </button>
          </div>
          <p className="muted" style={{ marginTop: 6 }}>
            Melhor resultado: foto nítida, bem iluminada, <b>um</b> rosto de
            frente, testa e cabelo visíveis. Evite close de cima, de lado ou
            rosto tapado. A arte é fotográfica, com a criança igual à foto — o mesmo
            personagem nas páginas e no vídeo.
          </p>

          <h3 className="field-label">Personagens Extras (amigos, irmãos, etc.)</h3>
          <div className="upload">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setExtraCharFile(e.target.files?.[0] ?? null)}
            />
            <input
              value={extraCharName}
              onChange={(e) => setExtraCharName(e.target.value)}
              placeholder="Nome do personagem"
              maxLength={40}
              style={{ flex: 1, minWidth: 120 }}
            />
            <button disabled={!extraCharFile || locked || !mediaConsent} onClick={uploadExtraCharacter}>
              Adicionar
            </button>
          </div>
          {extraChars.length > 0 && (
            <div style={{ margin: "8px 0" }}>
              <p className="muted">{extraChars.length} personagem(ns) extra(s) adicionado(s)</p>
              <button disabled={locked} onClick={generateExtraCharacters}>
                Gerar ilustrações dos extras <span className="muted">(1 crédito cada)</span>
              </button>
            </div>
          )}

          <h3 className="field-label">História</h3>
          <div className="styles">
            <button
              className={`chip ${storyMode === "invent" ? "on" : ""}`}
              onClick={() => setStoryMode("invent")}
            >
              ✨ Inventar com IA
            </button>
            <button
              className={`chip ${storyMode === "write" ? "on" : ""}`}
              onClick={() => setStoryMode("write")}
            >
              ✍️ Escrever a minha
            </button>
            <button
              className={`chip ${storyMode === "file" ? "on" : ""}`}
              onClick={() => setStoryMode("file")}
            >
              📄 Enviar arquivo
            </button>
            <button
              className={`chip ${storyMode === "catalog" ? "on" : ""}`}
              onClick={openCatalog}
            >
              📚 Histórias prontas
            </button>
          </div>

          {storyMode === "invent" && (
            <button disabled={locked} onClick={() => runStep("story")} data-testid="studio-generate-story">
              Gerar história com IA <span className="muted">(1 crédito)</span>
            </button>
          )}

          {storyMode === "catalog" && (
            <div className="story-catalog">
              {!templates && <p className="muted">Carregando catálogo…</p>}
              {templates && !project?.child_name && (
                <p className="muted">
                  Defina o nome da criança ao criar o projeto — ele entra no título e no texto.
                </p>
              )}
              {templates?.map((t) => (
                <div
                  key={t.id}
                  className="catalog-item"
                  style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "8px 0", borderBottom: "1px solid var(--border, #333)",
                  }}
                >
                  <span style={{ fontSize: 22 }}>{t.emoji}</span>
                  <div style={{ flex: 1 }}>
                    <strong>
                      {t.titulo.replace("{NOME}", project?.child_name || "{nome}")}
                    </strong>
                    <div className="muted" style={{ fontSize: 12 }}>
                      {t.tematica} · {t.idade} anos · {t.paginas} páginas
                      {t.genero !== "unissex" ? ` · ${t.genero}` : ""}
                    </div>
                  </div>
                  <button
                    disabled={locked || !project}
                    onClick={() => applyTemplate(t.id)}
                  >
                    {appliedTemplate === t.id ? "✓ Aplicada" : "Usar"}
                    {appliedTemplate !== t.id && <span className="muted"> (grátis)</span>}
                  </button>
                </div>
              ))}
            </div>
          )}

          {storyMode === "file" && (
            <div className="upload">
              <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={onStoryFile} />
              <span className="muted">PDF, DOCX ou TXT (até 5MB)</span>
            </div>
          )}

          {(storyMode === "write" || storyMode === "file") && (
            <div className="story-write">
              <textarea
                className="story-input"
                rows={8}
                style={{ width: "100%", boxSizing: "border-box", resize: "vertical" }}
                placeholder="Escreva ou cole a sua história aqui. Dica: separe as páginas com 'Página 1:', 'Página 2:'..."
                value={storyText}
                onChange={(e) => setStoryText(e.target.value)}
              />
              <button disabled={locked || !storyText.trim()} onClick={saveStory}>
                Salvar história
              </button>
            </div>
          )}

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
            <p className="muted">Aprove o personagem para montar o e-book.</p>
          )}

          <ProgressList jobs={jobs} />

          {/* Resultado de cada etapa */}
          <div className="results">
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
              <div className="result-block">
                <h3 className="field-label">Personagens Extras</h3>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  {assets.extra_characters.map((ec, i) => (
                    <div key={i} style={{ textAlign: "center" }}>
                      <img
                        src={ec.url}
                        alt={ec.name}
                        style={{ width: 100, height: 100, objectFit: "cover", borderRadius: 50 }}
                      />
                      <p className="muted" style={{ margin: "4px 0 0" }}>{ec.name}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {project.story_text && (
              <div className="result-block" data-testid="studio-story-result">
                <h3 className="field-label">História</h3>
                <pre className="story" style={{ whiteSpace: "pre-wrap" }} data-testid="studio-story-text">{project.story_text}</pre>
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
              <div className="result-block">
                <h3 className="field-label">Vídeo</h3>
                <p className="muted">O clipe e o vídeo narrado usam o mesmo personagem 3D do livro.</p>
                <VideoStepButtons locked={locked} canMakeVideo={canMakeVideo} runStep={runStep} />
              </div>
            )}

            {assets?.video_url && (
              <div className="result-block">
                <h3 className="field-label">Animação</h3>
                {assets.video_url.toLowerCase().includes(".gif") ? (
                  <img
                    src={assets.video_url}
                    alt="Animação"
                    style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                  />
                ) : (
                  <video src={assets.video_url} controls style={{ maxWidth: 360, width: "100%" }} />
                )}
              </div>
            )}

            {assets?.narrated_video_url && (
              <div className="result-block">
                <h3 className="field-label">Vídeo narrado</h3>
                {assets.narrated_video_url.toLowerCase().includes(".gif") ? (
                  <img
                    src={assets.narrated_video_url}
                    alt="Vídeo narrado"
                    style={{ maxWidth: 360, width: "100%", borderRadius: 12 }}
                  />
                ) : (
                  <video
                    src={assets.narrated_video_url}
                    controls
                    style={{ maxWidth: 360, width: "100%" }}
                  />
                )}
              </div>
            )}
          </div>

          <button className="link" onClick={() => (isDemo ? exitDemo() : setProject(null))}>
            {isDemo ? "← Criar a minha história" : "← Novo projeto"}
          </button>
        </section>
      )}
    </div>
  );
}
