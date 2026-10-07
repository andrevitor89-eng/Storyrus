import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { api } from "./api";
import type { UserVoice } from "./types";
import { colors, fonts, radii, space } from "./theme";

type Props = {
  busy: boolean;
  mediaConsent: boolean;
  voices: UserVoice[];
  customVoiceAvailable: boolean;
  selectedVoiceId: string;
  voiceName: string;
  onSelectVoice: (id: string) => void;
  onVoiceName: (name: string) => void;
  onUploaded: (voice: UserVoice) => void | Promise<void>;
  onRemove: () => void;
  onError: (msg: string) => void;
};

/** Seleção / clone de voz para vídeo narrado (paridade com VoiceNarrationPanel do web). */
export function VoicePanel({
  busy,
  mediaConsent,
  voices,
  customVoiceAvailable,
  selectedVoiceId,
  voiceName,
  onSelectVoice,
  onVoiceName,
  onUploaded,
  onRemove,
  onError,
}: Props) {
  const [uploading, setUploading] = useState(false);

  async function pickAndUpload() {
    if (!mediaConsent) {
      onError("Marque o consentimento antes de enviar áudio.");
      return;
    }
    const res = await DocumentPicker.getDocumentAsync({
      type: ["audio/*"],
      copyToCacheDirectory: true,
    });
    if (res.canceled || !res.assets?.[0]) return;
    const asset = res.assets[0];
    setUploading(true);
    try {
      const voice = await api.uploadVoice(
        asset.uri,
        voiceName.trim() || "Minha voz",
        asset.mimeType || "audio/mpeg",
        voices.length === 0,
      );
      await onUploaded(voice);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <View style={s.block}>
      <Text style={s.h3}>Voz da narração</Text>
      {!customVoiceAvailable ? (
        <Text style={s.muted}>Clone de voz indisponível neste ambiente.</Text>
      ) : (
        <>
          <Text style={s.muted}>
            Envie um áudio curto (mp3/m4a/wav) para narrar o vídeo com a sua voz.
          </Text>
          <TextInput
            style={s.input}
            value={voiceName}
            onChangeText={onVoiceName}
            placeholder="Nome da voz"
            placeholderTextColor={colors.placeholder}
            editable={!busy && !uploading}
          />
          <Pressable
            style={[s.btnAlt, (busy || uploading || !mediaConsent) && s.disabled]}
            onPress={() => void pickAndUpload()}
            disabled={busy || uploading || !mediaConsent}
          >
            <Text style={s.btnText}>{uploading ? "Clonando…" : "Enviar áudio"}</Text>
          </Pressable>
          {voices.length > 0 && (
            <View style={s.chips}>
              <Pressable
                style={[s.chip, !selectedVoiceId && s.chipOn]}
                onPress={() => onSelectVoice("")}
                disabled={busy}
              >
                <Text style={[s.chipText, !selectedVoiceId && s.chipTextOn]}>Automática</Text>
              </Pressable>
              {voices.map((v) => {
                const on = selectedVoiceId === v.id;
                return (
                  <Pressable
                    key={v.id}
                    style={[s.chip, on && s.chipOn]}
                    onPress={() => onSelectVoice(v.id)}
                    disabled={busy}
                  >
                    <Text style={[s.chipText, on && s.chipTextOn]}>
                      {v.name}
                      {v.is_default ? " ★" : ""}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
          {selectedVoiceId ? (
            <Pressable onPress={onRemove} disabled={busy} style={s.linkBtn}>
              <Text style={s.link}>Remover voz selecionada</Text>
            </Pressable>
          ) : null}
        </>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  block: { gap: space.sm },
  h3: {
    color: colors.text,
    fontSize: 16,
    fontFamily: fonts.displaySemi,
  },
  muted: { color: colors.muted, fontSize: 13, fontFamily: fonts.body, lineHeight: 20 },
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
  btnAlt: {
    backgroundColor: colors.secondary,
    borderRadius: radii.pill,
    minHeight: 48,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  disabled: { opacity: 0.5 },
  btnText: { color: colors.white, fontFamily: fonts.displaySemi, fontSize: 15 },
  linkBtn: { paddingVertical: 8 },
  link: { color: colors.primary, fontFamily: fonts.bodySemi },
});
