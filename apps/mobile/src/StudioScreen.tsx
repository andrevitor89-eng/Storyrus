import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Image,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as ImagePicker from "expo-image-picker";
import { api } from "./api";
import { THEMES, THEME_GROUP_LABEL, themeLabel } from "./themes";
import { VoicePanel } from "./VoicePanel";
import type { Job, Project, ProjectAssets, StudioStep, Theme, ThemeGroup, UserVoice } from "./types";
import { colors, fonts, logo, radii, space } from "./theme";

const STEPS: { key: StudioStep; label: string; cost: number }[] = [
  { key: "avatar", label: "Gerar personagem", cost: 1 },
  { key: "story", label: "Escrever história", cost: 1 },
  { key: "ebook", label: "Montar ebook", cost: 1 },
  { key: "video", label: "Gerar vídeo", cost: 5 },
  { key: "narrated-video", label: "Vídeo narrado", cost: 8 },
];

const DOT: Record<string, string> = {
  PENDING: colors.hint,
  RUNNING: colors.running,
  DONE: colors.ok,
  FAILED: colors.error,
};

const GROUPS: ThemeGroup[] = ["aventura", "datas", "educativo"];

export function StudioScreen({
  onLogout,
  bootError,
}: {
  onLogout: () => void | Promise<void>;
  bootError?: string | null;
}) {
  const insets = useSafeAreaInsets();
  const [credits, setCredits] = useState<number | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [assets, setAssets] = useState<ProjectAssets | null>(null);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [mediaConsent, setMediaConsent] = useState(false);
  const [selectedThemes, setSelectedThemes] = useState<Theme[]>(["adventure"]);
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState("");
  const [dedication, setDedication] = useState("");
  const [voices, setVoices] = useState<UserVoice[]>([]);
  const [customVoiceAvailable, setCustomVoiceAvailable] = useState(false);
  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [voiceName, setVoiceName] = useState("Minha voz");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  const theme = selectedThemes[0] ?? "adventure";
  const extraTheme = selectedThemes[1];
  const characterApproved = !!project?.character_approved_at;
  const bookApproved = !!project?.book_approved_at;
  const printRequested = !!project?.print_requested_at;

  const refreshCredits = useCallback(async () => {
    try {
      setCredits((await api.credits()).credits);
    } catch {
      /* ignore */
    }
  }, []);

  const refreshVoices = useCallback(async () => {
    try {
      const data = await api.listVoices();
      setVoices(data.items);
      setCustomVoiceAvailable(data.custom_voice_available);
      setSelectedVoiceId((prev) => {
        if (prev && data.items.some((v) => v.id === prev)) return prev;
        const def = data.items.find((v) => v.is_default);
        return def?.id || data.items[0]?.id || "";
      });
    } catch {
      /* ignore */
    }
  }, []);

  const refreshAssets = useCallback(async (projectId: string) => {
    try {
      setAssets(await api.getAssets(projectId));
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    refreshCredits();
    refreshVoices();
  }, [refreshCredits, refreshVoices]);

  useEffect(() => {
    if (!project) return;
    const active = jobs.some((j) => j.status === "PENDING" || j.status === "RUNNING");
    if (!active) {
      if (poll.current) clearInterval(poll.current);
      void refreshAssets(project.id);
      return;
    }
    poll.current = setInterval(async () => {
      try {
        const [p, js] = await Promise.all([api.getProject(project.id), api.listJobs(project.id)]);
        setProject(p);
        setJobs(js);
        refreshCredits();
        const stillActive = js.some((j) => j.status === "PENDING" || j.status === "RUNNING");
        if (!stillActive) void refreshAssets(project.id);
      } catch {
        /* ignore */
      }
    }, 2500);
    return () => {
      if (poll.current) clearInterval(poll.current);
    };
  }, [project, jobs, refreshCredits, refreshAssets]);

  function toggleTheme(id: Theme) {
    setSelectedThemes((prev) => {
      if (prev.includes(id)) {
        const next = prev.filter((t) => t !== id);
        return next.length ? next : prev;
      }
      if (prev.length >= 2) return [prev[0], id];
      return [...prev, id];
    });
  }

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const ageNum = childAge.trim() ? Number(childAge) : undefined;
      const p = await api.createProject(
        theme,
        extraTheme,
        childName,
        dedication,
        Number.isFinite(ageNum) ? ageNum : undefined,
      );
      setProject(p);
      setJobs([]);
      setAssets(null);
      setPhotoUploaded(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function pickAndUpload() {
    if (!project) return;
    if (!mediaConsent) {
      setError("Marque o consentimento antes de enviar a foto.");
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
    });
    if (res.canceled) return;
    setBusy(true);
    setError(null);
    try {
      const asset = res.assets[0];
      const ext = asset.uri.split(".").pop() || "jpg";
      const u = await api.requestPhotoUpload(project.id, asset.mimeType || "image/jpeg", ext);
      await api.uploadToSignedUrl(u.upload_url, asset.uri, asset.mimeType || "image/jpeg");
      setPhotoUploaded(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function runStep(step: StudioStep) {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      let body: Record<string, unknown> = {};
      if (step === "video") body = { duration_s: 30 };
      if (step === "narrated-video" && selectedVoiceId) body = { voice_id: selectedVoiceId };
      await api.startStep(project.id, step, body);
      setJobs(await api.listJobs(project.id));
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function approveCharacter() {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      setProject(await api.approveCharacter(project.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function approveBook() {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      setProject(await api.approveBook(project.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function requestPrint() {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      setProject(await api.requestPrint(project.id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onVoiceUploaded(voice: UserVoice) {
    await refreshVoices();
    setSelectedVoiceId(voice.id);
  }

  async function removeSelectedVoice() {
    if (!selectedVoiceId) return;
    setError(null);
    try {
      await api.deleteVoice(selectedVoiceId);
      await refreshVoices();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function openUrl(url: string | null | undefined) {
    if (!url) return;
    void Linking.openURL(url);
  }

  function resetProject() {
    setProject(null);
    setJobs([]);
    setAssets(null);
    setPhotoUploaded(false);
  }

  return (
    <ScrollView
      style={s.screen}
      contentContainerStyle={[
        s.content,
        { paddingBottom: Math.max(insets.bottom, space.lg) + 16 },
      ]}
      keyboardShouldPersistTaps="handled"
    >
      <View style={s.header}>
        <Image source={logo} style={s.hdrLogo} resizeMode="contain" />
        <View style={s.headerMeta}>
          <View style={s.creditsPill}>
            <Text style={s.creditsText}>Créditos: {credits ?? "…"}</Text>
          </View>
          <Pressable onPress={() => void onLogout()} style={s.logoutBtn} hitSlop={8}>
            <Text style={s.link}>Sair</Text>
          </Pressable>
        </View>
      </View>

      {bootError && <Text style={s.error}>{bootError}</Text>}
      {error && <Text style={s.error}>{error}</Text>}

      {!project ? (
        <View style={s.card}>
          <Text style={s.h2}>Novo projeto</Text>
          <Text style={s.muted}>
            Escolha até 2 temas. O 1º define a aventura; o 2º só acrescenta um aprendizado.
          </Text>

          {GROUPS.map((group) => (
            <View key={group} style={s.groupBlock}>
              <Text style={s.group}>{THEME_GROUP_LABEL[group]}</Text>
              <View style={s.chips}>
                {THEMES.filter((t) => t.group === group).map((t) => {
                  const on = selectedThemes.includes(t.id);
                  const ord = selectedThemes.indexOf(t.id);
                  return (
                    <Pressable
                      key={t.id}
                      style={[s.chip, on && s.chipOn]}
                      onPress={() => toggleTheme(t.id)}
                    >
                      <Text style={[s.chipText, on && s.chipTextOn]}>
                        {t.emoji} {t.label}
                        {ord === 0 ? " ·1" : ord === 1 ? " ·2" : ""}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          ))}

          <Text style={s.h3}>Nome, idade e dedicatória</Text>
          <Text style={s.label}>Nome da criança</Text>
          <TextInput
            style={s.input}
            value={childName}
            onChangeText={setChildName}
            placeholder="Nome"
            placeholderTextColor={colors.placeholder}
          />
          <Text style={s.label}>Idade</Text>
          <TextInput
            style={s.input}
            value={childAge}
            onChangeText={setChildAge}
            placeholder="Ex.: 5"
            placeholderTextColor={colors.placeholder}
            keyboardType="number-pad"
          />
          <Text style={s.label}>Dedicatória</Text>
          <TextInput
            style={[s.input, s.inputMulti]}
            value={dedication}
            onChangeText={setDedication}
            placeholder="Página 2 do livro"
            placeholderTextColor={colors.placeholder}
            multiline
          />

          <Pressable style={[s.btn, busy && s.disabled]} onPress={start} disabled={busy}>
            <Text style={s.btnText}>Criar projeto</Text>
          </Pressable>
        </View>
      ) : (
        <>
          <View style={s.card}>
            <Text style={s.h2}>Projeto ativo</Text>
            <Text style={s.muted}>
              Tema: {themeLabel(project.theme)}
              {project.extra_theme ? ` + ${themeLabel(project.extra_theme)}` : ""}
              {project.child_name ? ` · ${project.child_name}` : ""}
              {" · "}Status: {project.status}
            </Text>

            <Pressable
              style={[s.consent, mediaConsent && s.consentOn]}
              onPress={() => setMediaConsent((v) => !v)}
            >
              <View style={[s.checkbox, mediaConsent && s.checkboxOn]}>
                {mediaConsent ? <Text style={s.checkMark}>✓</Text> : null}
              </View>
              <Text style={s.muted}>
                Sou o responsável legal e autorizo o uso desta foto (e voz, se clonada) só para criar
                este livro.
              </Text>
            </Pressable>

            <Pressable
              style={[s.btnAlt, (!mediaConsent || busy) && s.disabled]}
              onPress={pickAndUpload}
              disabled={busy || !mediaConsent}
            >
              <Text style={s.btnText}>{photoUploaded ? "Foto enviada ✓" : "Enviar foto"}</Text>
            </Pressable>
          </View>

          <View style={s.card}>
            <Text style={s.h2}>Etapas</Text>
            <View style={s.steps}>
              {STEPS.map((st) => {
                const needPhoto = st.key === "avatar" && !photoUploaded;
                const needChar =
                  (st.key === "ebook" || st.key === "video" || st.key === "narrated-video") &&
                  !characterApproved;
                const disabled = busy || needPhoto || needChar;
                return (
                  <Pressable
                    key={st.key}
                    style={[s.btn, disabled && s.disabled]}
                    onPress={() => runStep(st.key)}
                    disabled={disabled}
                  >
                    <Text style={s.btnText}>
                      {st.label} ({st.cost} créd.)
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            {!characterApproved && photoUploaded ? (
              <Text style={s.hint}>Aprove o personagem antes do ebook / vídeos.</Text>
            ) : null}
          </View>

          <View style={s.card}>
            <VoicePanel
              busy={busy}
              mediaConsent={mediaConsent}
              voices={voices}
              customVoiceAvailable={customVoiceAvailable}
              selectedVoiceId={selectedVoiceId}
              voiceName={voiceName}
              onSelectVoice={setSelectedVoiceId}
              onVoiceName={setVoiceName}
              onUploaded={onVoiceUploaded}
              onRemove={() => void removeSelectedVoice()}
              onError={setError}
            />
          </View>

          {jobs.length > 0 && (
            <View style={s.card}>
              <Text style={s.h2}>Jobs</Text>
              {jobs.map((j) => (
                <View key={j.id} style={s.job}>
                  <View style={[s.dot, { backgroundColor: DOT[j.status] }]} />
                  <Text style={s.jtype}>{j.type}</Text>
                  <Text style={s.muted}>{j.status}</Text>
                  {j.error ? <Text style={s.error}>{j.error}</Text> : null}
                </View>
              ))}
              {busy && <ActivityIndicator color={colors.primary} />}
            </View>
          )}

          {(assets?.character_url || assets?.realistic_url) && (
            <View style={s.card}>
              <Text style={s.h2}>Personagem</Text>
              <Image
                source={{ uri: (assets.character_url || assets.realistic_url)! }}
                style={s.preview}
                resizeMode="cover"
              />
              {characterApproved ? (
                <Text style={s.ok}>Personagem aprovado ✓</Text>
              ) : (
                <Pressable
                  style={[s.btnAlt, busy && s.disabled]}
                  onPress={() => void approveCharacter()}
                  disabled={busy}
                >
                  <Text style={s.btnText}>Aprovar personagem</Text>
                </Pressable>
              )}
            </View>
          )}

          {(assets?.ebook_url || project.ebook_url || (assets?.page_images?.length ?? 0) > 0) && (
            <View style={s.card}>
              <Text style={s.h2}>Livro</Text>
              <View style={s.thumbs}>
                {assets?.page_images?.slice(0, 4).map((u, i) => (
                  <Image key={i} source={{ uri: u }} style={s.pageThumb} resizeMode="cover" />
                ))}
              </View>
              {(assets?.ebook_url || project.ebook_url) && (
                <Pressable
                  onPress={() => openUrl(assets?.ebook_url || project.ebook_url)}
                  style={s.linkBtn}
                >
                  <Text style={s.link}>Abrir ebook PDF</Text>
                </Pressable>
              )}
              {bookApproved ? (
                <Text style={s.ok}>Livro aprovado ✓</Text>
              ) : (
                <Pressable
                  style={[s.btnAlt, (!(assets?.ebook_url || project.ebook_url) || busy) && s.disabled]}
                  onPress={() => void approveBook()}
                  disabled={busy || !(assets?.ebook_url || project.ebook_url)}
                >
                  <Text style={s.btnText}>Aprovar livro</Text>
                </Pressable>
              )}
              {bookApproved &&
                (printRequested ? (
                  <Text style={s.ok}>Impressão solicitada ✓</Text>
                ) : (
                  <Pressable
                    style={[s.btnAlt, busy && s.disabled]}
                    onPress={() => void requestPrint()}
                    disabled={busy}
                  >
                    <Text style={s.btnText}>Pedir impressão</Text>
                  </Pressable>
                ))}
            </View>
          )}

          {project.story_text ? (
            <View style={s.card}>
              <Text style={s.h2}>História</Text>
              <Text style={s.story}>{project.story_text}</Text>
            </View>
          ) : null}

          {((assets?.video_url || project.video_url) ||
            (assets?.narrated_video_url || project.narrated_video_url)) && (
            <View style={s.card}>
              <Text style={s.h2}>Vídeos</Text>
              {(assets?.video_url || project.video_url) && (
                <Pressable
                  onPress={() => openUrl(assets?.video_url || project.video_url)}
                  style={s.linkBtn}
                >
                  <Text style={s.ok}>Abrir vídeo</Text>
                </Pressable>
              )}
              {(assets?.narrated_video_url || project.narrated_video_url) && (
                <Pressable
                  onPress={() =>
                    openUrl(assets?.narrated_video_url || project.narrated_video_url)
                  }
                  style={s.linkBtn}
                >
                  <Text style={s.ok}>Abrir vídeo narrado</Text>
                </Pressable>
              )}
            </View>
          )}

          <Pressable onPress={resetProject} style={s.linkBtn}>
            <Text style={s.link}>← Novo projeto</Text>
          </Pressable>
        </>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.md },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 4,
    gap: 12,
  },
  hdrLogo: { width: 52, height: 52 },
  headerMeta: { flexDirection: "row", alignItems: "center", gap: 10, flexShrink: 1 },
  creditsPill: {
    backgroundColor: colors.input,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.pill,
    paddingHorizontal: 12,
    paddingVertical: 8,
    minHeight: 36,
    justifyContent: "center",
  },
  creditsText: { color: colors.muted, fontFamily: fonts.bodySemi, fontSize: 13 },
  logoutBtn: { paddingVertical: 8, paddingHorizontal: 4, minHeight: 44, justifyContent: "center" },
  card: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.xl,
    padding: space.lg,
    gap: space.sm,
  },
  h2: { color: colors.text, fontSize: 20, fontFamily: fonts.display },
  h3: { color: colors.text, fontSize: 16, fontFamily: fonts.displaySemi, marginTop: 6 },
  label: { color: colors.group, fontFamily: fonts.bodySemi, fontSize: 13, marginTop: 2 },
  group: { color: colors.group, fontSize: 13, fontFamily: fonts.bodySemi },
  groupBlock: { gap: 8 },
  muted: { color: colors.muted, flexShrink: 1, fontFamily: fonts.body, lineHeight: 20 },
  hint: { color: colors.hint, fontSize: 13, fontFamily: fonts.bodySemi },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    backgroundColor: colors.input,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.pill,
    paddingVertical: 10,
    paddingHorizontal: 14,
    minHeight: 40,
    justifyContent: "center",
  },
  chipOn: { backgroundColor: colors.teal, borderColor: colors.teal },
  chipText: { color: colors.text, fontSize: 13, fontFamily: fonts.bodySemi },
  chipTextOn: { color: colors.white },
  input: {
    backgroundColor: colors.input,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: 14,
    paddingVertical: 12,
    minHeight: 48,
    color: colors.text,
    fontFamily: fonts.body,
    fontSize: 16,
  },
  inputMulti: { minHeight: 72, textAlignVertical: "top" },
  consent: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
    backgroundColor: colors.input,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.md,
    padding: 12,
  },
  consentOn: { borderColor: colors.teal },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: colors.teal,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  checkboxOn: { backgroundColor: colors.teal, borderColor: colors.teal },
  checkMark: { color: colors.white, fontWeight: "700", fontSize: 14, lineHeight: 16 },
  steps: { gap: 10 },
  btn: {
    backgroundColor: colors.primary,
    borderRadius: radii.pill,
    minHeight: 50,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  btnAlt: {
    backgroundColor: colors.secondary,
    borderRadius: radii.pill,
    minHeight: 50,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  disabled: { opacity: 0.5 },
  btnText: { color: colors.white, fontFamily: fonts.displaySemi, fontSize: 15 },
  linkBtn: { paddingVertical: 10 },
  link: { color: colors.primary, fontFamily: fonts.bodySemi, fontSize: 15 },
  job: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 6,
    flexWrap: "wrap",
  },
  dot: { width: 10, height: 10, borderRadius: 5 },
  jtype: { color: colors.text, fontFamily: fonts.bodySemi, minWidth: 90 },
  story: {
    color: colors.text,
    backgroundColor: colors.input,
    padding: 14,
    borderRadius: radii.md,
    fontFamily: fonts.body,
    lineHeight: 22,
  },
  ok: { color: colors.ok, fontFamily: fonts.bodySemi },
  error: { color: colors.error, fontFamily: fonts.bodySemi, lineHeight: 20 },
  thumbs: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  preview: {
    width: "100%",
    height: 220,
    borderRadius: radii.lg,
    backgroundColor: colors.input,
  },
  pageThumb: {
    width: 96,
    height: 96,
    borderRadius: radii.sm,
    backgroundColor: colors.input,
  },
});
