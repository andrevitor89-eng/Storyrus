import { useState, type ComponentProps } from "react";
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { api, type SignupPayload } from "./api";
import { colors, fonts, logo, radii, space } from "./theme";

function Field({
  label,
  ...props
}: { label: string } & ComponentProps<typeof TextInput>) {
  return (
    <View style={s.field}>
      <Text style={s.label}>{label}</Text>
      <TextInput
        style={s.input}
        placeholderTextColor={colors.placeholder}
        {...props}
      />
    </View>
  );
}

/** Login/signup obrigatório antes do estúdio. */
export function AuthScreen({
  onAuthed,
  initialMode = "login",
}: {
  onAuthed: () => void;
  initialMode?: "login" | "signup";
}) {
  const insets = useSafeAreaInsets();
  const [mode, setMode] = useState<"login" | "signup">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [street, setStreet] = useState("");
  const [number, setNumber] = useState("");
  const [complement, setComplement] = useState("");
  const [district, setDistrict] = useState("");
  const [city, setCity] = useState("");
  const [stateUf, setStateUf] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [checkEmail, setCheckEmail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      if (mode === "signup") {
        if (password !== passwordConfirm) {
          setError("As senhas não coincidem.");
          return;
        }
        if (!acceptTerms) {
          setError("Aceite os termos e a política de privacidade.");
          return;
        }
        const payload: SignupPayload = {
          email: email.trim(),
          password,
          password_confirm: passwordConfirm,
          full_name: fullName.trim(),
          phone: phone.trim(),
          postal_code: postalCode.trim(),
          street: street.trim(),
          number: number.trim(),
          complement: complement.trim() || null,
          district: district.trim(),
          city: city.trim(),
          state: stateUf.trim().toUpperCase(),
          accept_terms: true,
        };
        await api.signup(payload);
        setCheckEmail(true);
        return;
      }
      await api.login(email.trim(), password);
      onAuthed();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (checkEmail) {
    return (
      <View style={[s.wrap, { paddingBottom: Math.max(insets.bottom, space.xl) }]}>
        <Image source={logo} style={s.logo} resizeMode="contain" />
        <Text style={s.brand}>Story R Us</Text>
        <Text style={s.title}>Verifique seu e-mail</Text>
        <Text style={s.muted}>
          Enviamos um link de confirmação. Ative a conta e depois entre com e-mail e senha.
        </Text>
        <Pressable
          style={s.linkBtn}
          onPress={() => {
            setCheckEmail(false);
            setMode("login");
          }}
        >
          <Text style={s.link}>Já confirmei — entrar</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={s.flex}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={[
          s.wrap,
          { paddingBottom: Math.max(insets.bottom, space.xl) + 12 },
        ]}
        keyboardShouldPersistTaps="handled"
      >
        <Image source={logo} style={s.logo} resizeMode="contain" />
        <Text style={s.brand}>Story R Us</Text>
        <Text style={s.title}>{mode === "signup" ? "Criar conta" : "Entrar"}</Text>
        <Text style={s.muted}>
          É preciso ter uma conta para criar livros personalizados.
        </Text>

        <View style={s.card}>
          {mode === "signup" && (
            <Field
              label="Nome completo"
              placeholder="Seu nome"
              value={fullName}
              onChangeText={setFullName}
            />
          )}

          <Field
            label="E-mail"
            placeholder="voce@email.com"
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
          />

          {mode === "signup" && (
            <Field
              label="Telefone / WhatsApp"
              placeholder="+55 …"
              keyboardType="phone-pad"
              value={phone}
              onChangeText={setPhone}
            />
          )}

          <Field
            label="Senha"
            placeholder="Mínimo 8 caracteres"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />

          {mode === "signup" && (
            <>
              <Field
                label="Confirmar senha"
                placeholder="Repita a senha"
                secureTextEntry
                value={passwordConfirm}
                onChangeText={setPasswordConfirm}
              />
              <Field
                label="CEP"
                placeholder="00000-000"
                keyboardType="number-pad"
                value={postalCode}
                onChangeText={setPostalCode}
              />
              <Field label="Rua" placeholder="Rua" value={street} onChangeText={setStreet} />
              <Field
                label="Número"
                placeholder="Nº"
                value={number}
                onChangeText={setNumber}
              />
              <Field
                label="Complemento"
                placeholder="Opcional"
                value={complement}
                onChangeText={setComplement}
              />
              <Field
                label="Bairro"
                placeholder="Bairro"
                value={district}
                onChangeText={setDistrict}
              />
              <Field label="Cidade" placeholder="Cidade" value={city} onChangeText={setCity} />
              <Field
                label="UF"
                placeholder="SP"
                autoCapitalize="characters"
                maxLength={2}
                value={stateUf}
                onChangeText={(v) => setStateUf(v.toUpperCase())}
              />
              <Pressable style={s.termsRow} onPress={() => setAcceptTerms(!acceptTerms)}>
                <View style={[s.checkbox, acceptTerms && s.checkboxOn]}>
                  {acceptTerms ? <Text style={s.checkMark}>✓</Text> : null}
                </View>
                <Text style={s.termsText}>
                  Aceito os termos de uso e a política de privacidade
                </Text>
              </Pressable>
            </>
          )}

          {error && <Text style={s.error}>{error}</Text>}

          <Pressable
            style={[s.btn, busy && s.disabled]}
            onPress={submit}
            disabled={busy}
          >
            {busy ? (
              <ActivityIndicator color={colors.white} />
            ) : (
              <Text style={s.btnText}>{mode === "signup" ? "Criar conta" : "Entrar"}</Text>
            )}
          </Pressable>
        </View>

        <Pressable
          style={s.linkBtn}
          onPress={() => {
            setMode(mode === "signup" ? "login" : "signup");
            setCheckEmail(false);
            setError(null);
          }}
        >
          <Text style={s.link}>{mode === "signup" ? "Já tenho conta" : "Criar uma conta"}</Text>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  wrap: {
    flexGrow: 1,
    justifyContent: "center",
    paddingHorizontal: space.lg,
    paddingTop: space.xl,
    gap: space.sm,
    backgroundColor: colors.bg,
  },
  logo: { width: 96, height: 96, alignSelf: "center", marginBottom: 4 },
  brand: {
    color: colors.text,
    fontSize: 28,
    fontFamily: fonts.display,
    textAlign: "center",
    marginBottom: 2,
  },
  title: {
    color: colors.text,
    fontSize: 20,
    fontFamily: fonts.displaySemi,
    textAlign: "center",
  },
  muted: {
    color: colors.muted,
    fontFamily: fonts.body,
    textAlign: "center",
    marginBottom: space.sm,
    lineHeight: 22,
  },
  card: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.xl,
    padding: space.lg,
    gap: space.md,
  },
  field: { gap: 6 },
  label: {
    color: colors.group,
    fontFamily: fonts.bodySemi,
    fontSize: 13,
  },
  input: {
    backgroundColor: colors.input,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: 14,
    paddingVertical: 13,
    minHeight: 48,
    color: colors.text,
    fontFamily: fonts.body,
    fontSize: 16,
  },
  termsRow: { flexDirection: "row", alignItems: "flex-start", gap: 12, marginTop: 4 },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: colors.teal,
    marginTop: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxOn: { backgroundColor: colors.teal, borderColor: colors.teal },
  checkMark: { color: colors.white, fontWeight: "700", fontSize: 14, lineHeight: 16 },
  termsText: {
    color: colors.muted,
    flex: 1,
    lineHeight: 20,
    fontFamily: fonts.body,
  },
  btn: {
    backgroundColor: colors.primary,
    borderRadius: radii.pill,
    minHeight: 52,
    paddingHorizontal: 18,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 4,
  },
  disabled: { opacity: 0.55 },
  btnText: {
    color: colors.white,
    fontFamily: fonts.display,
    fontSize: 17,
  },
  linkBtn: { paddingVertical: 12, alignItems: "center" },
  link: {
    color: colors.primary,
    textAlign: "center",
    fontFamily: fonts.bodySemi,
    fontSize: 15,
  },
  error: { color: colors.error, fontFamily: fonts.bodySemi, lineHeight: 20 },
});
