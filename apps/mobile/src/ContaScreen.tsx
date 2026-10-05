import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { api } from "./api";
import type { Project, UserVoice } from "./types";

type Me = {
  id: string;
  email: string;
  credits: number;
  created_at: string;
  is_guest: boolean;
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function ContaScreen({
  onBack,
  onLogout,
}: {
  onBack: () => void;
  onLogout: () => void | Promise<void>;
}) {
  const [me, setMe] = useState<Me | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [voices, setVoices] = useState<UserVoice[]>([]);
  const [customVoiceAvailable, setCustomVoiceAvailable] = useState(false);
  const [voiceName, setVoiceName] = useState("Minha voz");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [profile, projectList, voiceData] = await Promise.all([
        api.me(),
        api.listProjects(),
        api.listVoices(),
      ]);
      setMe(profile);
      setProjects(projectList);
      setVoices(voiceData.items);
      setCustomVoiceAvailable(voiceData.custom_voice_available);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSetDefault(id: string) {
    setBusy(true);
    setError(null);
    try {
      await api.setDefaultVoice(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onRemoveVoice(id: string) {
    setBusy(true);
    setError(null);
    try {
      await api.deleteVoice(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function pickAndUpload() {
    const res = await DocumentPicker.getDocumentAsync({
      type: ["audio/*"],
      copyToCacheDirectory: true,
    });
    if (res.canceled || !res.assets?.[0]) return;
    const asset = res.assets[0];
    setUploading(true);
    setError(null);
    try {
      await api.uploadVoice(
        asset.uri,
        voiceName.trim() || "Minha voz",
        asset.mimeType || "audio/mpeg",
        voices.length === 0,
      );
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }

  if (loading) {
    return (
      <View style={s.boot}>
        <ActivityIndicator color="#5b8cff" size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={s.screen} contentContainerStyle={{ padding: 20, gap: 12 }}>
      <View style={s.header}>
        <Text style={s.brand}>Conta</Text>
        <View style={{ flex: 1 }} />
        <Pressable onPress={onBack}>
          <Text style={s.link}>Estúdio</Text>
        </Pressable>
        <Pressable onPress={() => void onLogout()}>
          <Text style={s.link}>  Sair</Text>
        </Pressable>
      </View>

      {error && <Text style={s.error}>{error}</Text>}

      <View style={s.card}>
        <Text style={s.h2}>Dados</Text>
        <Text style={s.label}>E-mail</Text>
        <Text style={s.value}>{me?.email ?? "—"}</Text>
        <Text style={s.label}>Créditos</Text>
        <Text style={s.value}>{me?.credits ?? "—"}</Text>
        <Text style={s.label}>Membro desde</Text>
        <Text style={s.value}>{me?.created_at ? formatDate(me.created_at) : "—"}</Text>
      </View>

      <View style={s.card}>
        <Text style={s.h2}>Projetos</Text>
        {projects.length === 0 ? (
          <Text style={s.muted}>Nenhum projeto ainda. Crie um livro no estúdio.</Text>
        ) : (
          projects.map((project) => (
            <View key={project.id} style={s.row}>
              <View style={{ flex: 1, gap: 2 }}>
                <Text style={s.rowTitle}>{project.child_name?.trim() || "Sem nome"}</Text>
                <Text style={s.muted}>
                  {project.status} · {formatDate(project.created_at)}
                </Text>
              </View>
              <Pressable onPress={onBack}>
                <Text style={s.link}>Abrir</Text>
              </Pressable>
            </View>
          ))
        )}
      </View>

      <View style={s.card}>
        <Text style={s.h2}>Vozes</Text>
        {!customVoiceAvailable && voices.length === 0 ? (
          <Text style={s.muted}>Clone de voz indisponível neste ambiente.</Text>
        ) : (
          <>
            {customVoiceAvailable && (
              <View style={{ gap: 8 }}>
                <TextInput
                  style={s.input}
                  value={voiceName}
                  onChangeText={setVoiceName}
                  placeholder="Nome da voz"
                  placeholderTextColor="#6b7a9a"
                  editable={!busy && !uploading}
                />
                <Pressable
                  style={[s.btnAlt, (busy || uploading) && s.disabled]}
                  onPress={() => void pickAndUpload()}
                  disabled={busy || uploading}
                >
                  <Text style={s.btnText}>{uploading ? "Clonando…" : "Enviar áudio"}</Text>
                </Pressable>
              </View>
            )}
            {voices.length === 0 ? (
              <Text style={s.muted}>Nenhuma voz clonada ainda.</Text>
            ) : (
              voices.map((voice) => (
                <View key={voice.id} style={s.row}>
                  <View style={{ flex: 1, gap: 2 }}>
                    <Text style={s.rowTitle}>
                      {voice.name}
                      {voice.is_default ? " · Padrão" : ""}
                    </Text>
                    <Text style={s.muted}>{formatDate(voice.created_at)}</Text>
                  </View>
                  <View style={{ gap: 6, alignItems: "flex-end" }}>
                    {!voice.is_default && (
                      <Pressable disabled={busy} onPress={() => void onSetDefault(voice.id)}>
                        <Text style={s.link}>Padrão</Text>
                      </Pressable>
                    )}
                    <Pressable disabled={busy} onPress={() => void onRemoveVoice(voice.id)}>
                      <Text style={s.link}>Remover</Text>
                    </Pressable>
                  </View>
                </View>
              ))
            )}
          </>
        )}
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0f1320" },
  boot: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#0f1320" },
  header: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 },
  brand: { color: "#e8ecf5", fontSize: 20, fontWeight: "800" },
  link: { color: "#5b8cff", fontWeight: "600" },
  card: {
    backgroundColor: "#151b2d",
    borderColor: "#2a3550",
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    gap: 8,
  },
  h2: { color: "#e8ecf5", fontSize: 16, fontWeight: "700" },
  label: {
    color: "#93a0bd",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.6,
    textTransform: "uppercase",
    marginTop: 4,
  },
  value: { color: "#e8ecf5", fontSize: 15 },
  muted: { color: "#93a0bd", fontSize: 13 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "#2a3550",
  },
  rowTitle: { color: "#e8ecf5", fontSize: 14, fontWeight: "600" },
  input: {
    backgroundColor: "#0d1322",
    borderColor: "#2a3550",
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: "#e8ecf5",
  },
  btnAlt: { backgroundColor: "#334066", borderRadius: 8, padding: 12, alignItems: "center" },
  disabled: { opacity: 0.5 },
  btnText: { color: "#fff", fontWeight: "700" },
  error: { color: "#f87171", fontSize: 13 },
});
