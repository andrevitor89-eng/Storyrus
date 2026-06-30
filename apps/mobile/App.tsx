import { useState } from "react";
import { SafeAreaView, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";
import { AuthScreen } from "./src/AuthScreen";
import { StudioScreen } from "./src/StudioScreen";
import { setToken } from "./src/api";

export default function App() {
  const [authed, setAuthed] = useState(false);
  return (
    <SafeAreaView style={s.root}>
      <StatusBar style="light" />
      {authed ? (
        <StudioScreen
          onLogout={() => {
            setToken(null);
            setAuthed(false);
          }}
        />
      ) : (
        <AuthScreen onAuthed={() => setAuthed(true)} />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0f1320" },
});
