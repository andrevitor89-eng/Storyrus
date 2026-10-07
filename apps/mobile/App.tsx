import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { useFonts, Baloo2_600SemiBold, Baloo2_700Bold } from "@expo-google-fonts/baloo-2";
import {
  Quicksand_500Medium,
  Quicksand_600SemiBold,
  Quicksand_700Bold,
} from "@expo-google-fonts/quicksand";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { AuthScreen } from "./src/AuthScreen";
import { StudioScreen } from "./src/StudioScreen";
import { api, getToken, hydrateToken, logout, ensureSession } from "./src/api";
import { colors } from "./src/theme";

/**
 * Conta obrigatória: login/signup antes do estúdio.
 */
export default function App() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [bootError, setBootError] = useState<string | null>(null);
  const [fontsLoaded] = useFonts({
    Baloo2_600SemiBold,
    Baloo2_700Bold,
    Quicksand_500Medium,
    Quicksand_600SemiBold,
    Quicksand_700Bold,
  });

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
          setAuthed(!me.is_guest && me.email_verified);
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

  const booting = !ready || !fontsLoaded;

  return (
    <SafeAreaProvider>
      <SafeAreaView style={s.root} edges={["top", "left", "right"]}>
        <StatusBar style="light" />
        {booting ? (
          <View style={s.boot}>
            <ActivityIndicator color={colors.primary} size="large" />
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
    </SafeAreaProvider>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  boot: { flex: 1, alignItems: "center", justifyContent: "center" },
});
