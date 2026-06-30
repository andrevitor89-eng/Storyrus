import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { api } from "./api";
import type { Job, Project, Style } from "./types";

const STYLES: { id: Style; label: string }[] = [
  { id: "realistic", label: "Realista" },
  { id: "cartoon", label: "Desenho" },
  { id: "anime", label: "Animação" },
];
const STEPS: { key: "avatar" | "story" | "ebook" | "video"; label: string; cost: number }[] = [
  { key: "avatar", label: "Gerar personagem", cost: 1 },
  { key: "story", label: "Escrever história", cost: 1 },
  { key: "ebook", label: "Montar ebook", cost: 1 },
  { key: "video", label: "Gerar vídeo", cost: 5 },
];
const DOT: Record<string, string> = {
  PENDING: "#facc15",
  RUNNING: "#5b8cff",
  DONE: "#34d399",
  FAILED: "#f87171",
};

export function StudioScreen({ onLogout }: { onLogout: () => void }) {
  const [credits, setCredits] = useState<number | null>(null);
  const [style, setStyle] = useState<Style>("realistic");
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [photoUploaded, setPhotoUploaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

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

  useEffect(() => {
    if (!project) return;
    const active = jobs.some((j) => j.status === "PENDING" || j.status === "RUNNING");
    if (!active) {
      if (poll.current) clearInterval(poll.current);
      return;
    }
    poll.current = setInterval(async () => {
      try {
        const [p, js] = await Promise.all([api.getProject(project.id), api.listJobs(project.id)]);
        setProject(p);
        setJobs(js);
        refreshCredits();
      } catch {
        /* ignore */
      }
    }, 2500);
    return () => {
      if (poll.current) clearInterval(poll.current);
    };
  }, [project, jobs, refreshCredits]);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      setProject(await api.createProject(style));
      setJobs([]);
      setPhotoUploaded(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function pickAndUpload() {
    if (!project) return;
    const res = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images });
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

  async function runStep(step: "avatar" | "story" | "ebook" | "video") {
    if (!project) return;
    setBusy(true);
    setError(null);
    try {
      await api.startStep(project.id, step, step === "video" ? { duration_s: 30 } : {});
      setJobs(await api.listJobs(project.id));
      refreshCredits();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView style={s.screen} contentContainerStyle={{ padding: 20, gap: 12 }}>
      <View style={s.header}>
        <Text style={s.brand}>Histórias</Text>
        <View style={{ flex: 1 }} />
        <Text style={s.muted}>Créditos: {credits ?? "…"}</Text>
        <Pressable onPress={onLogout}>
          <Text style={s.link}>  Sair</Text>
        </Pressable>
      </View>

      {error && <Text style={s.error}>{error}</Text>}

      {!project ? (
        <View style={s.card}>
          <Text style={s.h2}>Novo projeto</Text>
          <Text style={s.muted}>Escolha o estilo:</Text>
          <View style={s.row}>
            {STYLES.map((st) => (
              <Pressable
                key={st.id}
                style={[s.chip, style === st.id && s.chipOn]}
                onPress={() => setStyle(st.id)}
              >
                <Text style={s.chipText}>{st.label}</Text>
              </Pressable>
            ))}
          </View>
          <Pressable style={s.btn} onPress={start} disabled={busy}>
            <Text style={s.btnText}>Criar projeto</Text>
          </Pressable>
        </View>
      ) : (
        <View style={s.card}>
          <Text style={s.h2}>Projeto</Text>
          <Text style={s.muted}>
            Estilo: {project.style} · Status: {project.status}
          </Text>

          <Pressable style={s.btnAlt} onPress={pickAndUpload} disabled={busy}>
            <Text style={s.btnText}>{photoUploaded ? "Foto enviada ✓" : "Enviar foto"}</Text>
          </Pressable>

          {STEPS.map((st) => {
            const disabled = busy || (st.key === "avatar" && !photoUploaded);
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

          {jobs.map((j) => (
            <View key={j.id} style={s.job}>
              <View style={[s.dot, { backgroundColor: DOT[j.status] }]} />
              <Text style={s.jtype}>{j.type}</Text>
              <Text style={s.muted}>{j.status}</Text>
              {j.error ? <Text style={s.error}>{j.error}</Text> : null}
            </View>
          ))}

          {busy && <ActivityIndicator color="#5b8cff" />}
          {project.story_text ? <Text style={s.story}>{project.story_text}</Text> : null}
          {project.ebook_url ? <Text style={s.ok}>Ebook: {project.ebook_url}</Text> : null}
          {project.video_url ? <Text style={s.ok}>Vídeo: {project.video_url}</Text> : null}

          <Pressable onPress={() => setProject(null)}>
            <Text style={s.link}>← Novo projeto</Text>
          </Pressable>
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0f1320" },
  header: { flexDirection: "row", alignItems: "center", paddingVertical: 8 },
  brand: { color: "#e8ecf5", fontWeight: "700", fontSize: 18 },
  card: { backgroundColor: "#182032", borderColor: "#2a3550", borderWidth: 1, borderRadius: 16, padding: 18, gap: 10 },
  h2: { color: "#e8ecf5", fontSize: 18, fontWeight: "700" },
  muted: { color: "#93a0bd" },
  row: { flexDirection: "row", gap: 8 },
  chip: { backgroundColor: "#0d1322", borderColor: "#2a3550", borderWidth: 1, borderRadius: 8, paddingVertical: 8, paddingHorizontal: 14 },
  chipOn: { backgroundColor: "#5b8cff", borderColor: "#5b8cff" },
  chipText: { color: "#e8ecf5" },
  btn: { backgroundColor: "#5b8cff", borderRadius: 8, padding: 12, alignItems: "center" },
  btnAlt: { backgroundColor: "#334066", borderRadius: 8, padding: 12, alignItems: "center" },
  disabled: { opacity: 0.5 },
  btnText: { color: "#fff", fontWeight: "700" },
  link: { color: "#5b8cff" },
  job: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 4 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  jtype: { color: "#e8ecf5", fontWeight: "600", width: 90 },
  story: { color: "#e8ecf5", backgroundColor: "#0d1322", padding: 12, borderRadius: 8 },
  ok: { color: "#34d399" },
  error: { color: "#f87171" },
});
