import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { api, setToken } from "./api";

export function AuthScreen({ onAuthed }: { onAuthed: () => void }) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const fn = mode === "signup" ? api.signup : api.login;
      const { access_token } = await fn(email.trim(), password);
      setToken(access_token);
      onAuthed();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={s.wrap}>
      <Text style={s.title}>Plataforma de Histórias</Text>
      <Text style={s.muted}>Foto → personagem → ebook → vídeo</Text>

      <TextInput
        style={s.input}
        placeholder="E-mail"
        placeholderTextColor="#93a0bd"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={s.input}
        placeholder="Senha (mín. 8)"
        placeholderTextColor="#93a0bd"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      {error && <Text style={s.error}>{error}</Text>}

      <Pressable style={s.btn} onPress={submit} disabled={busy}>
        {busy ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={s.btnText}>{mode === "signup" ? "Criar conta" : "Entrar"}</Text>
        )}
      </Pressable>

      <Pressable onPress={() => setMode(mode === "signup" ? "login" : "signup")}>
        <Text style={s.link}>{mode === "signup" ? "Já tenho conta" : "Criar uma conta"}</Text>
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, justifyContent: "center", padding: 24, gap: 10, backgroundColor: "#0f1320" },
  title: { color: "#e8ecf5", fontSize: 24, fontWeight: "700" },
  muted: { color: "#93a0bd", marginBottom: 12 },
  input: {
    backgroundColor: "#0d1322",
    borderColor: "#2a3550",
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    color: "#e8ecf5",
  },
  btn: { backgroundColor: "#5b8cff", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 6 },
  btnText: { color: "#fff", fontWeight: "700" },
  link: { color: "#5b8cff", textAlign: "center", marginTop: 12 },
  error: { color: "#f87171" },
});
