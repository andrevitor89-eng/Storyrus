import { useEffect, useState } from "react";
import { ActivityIndicator, SafeAreaView, StyleSheet, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { AuthScreen } from "./src/AuthScreen";
import { StudioScreen } from "./src/StudioScreen";
import { ensureGuest, hydrateToken, resetToGuest } from "./src/api";

/**
 * Guest-first (espelha o web): abre o estúdio com JWT de convidado.
 * Login/signup opcional via "Entrar"; "Sair" limpa e reminta guest.
 */
export default function App() {
  const [ready, setReady] = useState(false);
  const [bootError, setBootError] = useState<string | null>(null);
  const [showAuth, setShowAuth] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await hydrateToken();
        await ensureGuest();
        if (!cancelled) setBootError(null);
      } catch (e) {
        if (!cancelled) setBootError((e as Error).message);
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <SafeAreaView style={s.root}>
      <StatusBar style="light" />
      {!ready ? (
        <View style={s.boot}>
          <ActivityIndicator color="#5b8cff" size="large" />
        </View>
      ) : showAuth ? (
        <AuthScreen
          onAuthed={() => setShowAuth(false)}
          onSkip={() => setShowAuth(false)}
        />
      ) : (
        <StudioScreen
          bootError={bootError}
          onLogin={() => setShowAuth(true)}
          onLogout={async () => {
            try {
              await resetToGuest();
              setBootError(null);
            } catch (e) {
              setBootError((e as Error).message);
            }
          }}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0f1320" },
  boot: { flex: 1, alignItems: "center", justifyContent: "center" },
});
