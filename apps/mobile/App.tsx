import { useEffect, useState } from "react";
import { ActivityIndicator, SafeAreaView, StyleSheet, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { AuthScreen } from "./src/AuthScreen";
import { StudioScreen } from "./src/StudioScreen";
import { api, getToken, hydrateToken, logout, ensureSession } from "./src/api";

/**
 * Conta obrigatória: login/signup antes do estúdio.
 */
export default function App() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [bootError, setBootError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await hydrateToken();
        if (!getToken()) {
          if (!cancelled) {
            setAuthed(false);
            setBootError(null);
          }
          return;
        }
        await ensureSession();
        const me = await api.me();
        if (!cancelled) {
          setAuthed(!me.is_guest);
          setBootError(null);
        }
      } catch (e) {
        logout();
        if (!cancelled) {
          setAuthed(false);
          setBootError((e as Error).message);
        }
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
      ) : !authed ? (
        <AuthScreen
          onAuthed={() => {
            setAuthed(true);
            setBootError(null);
          }}
        />
      ) : (
        <StudioScreen
          bootError={bootError}
          onLogout={async () => {
            logout();
            setAuthed(false);
            setBootError(null);
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
