import { FormEvent, useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import logo from "./assets/logo.png";
import { accountGateHref } from "./Auth";
import { api, getToken, type MeUser, type ProfileUpdatePayload } from "./api";
import { formatCep, useCepLookup, type CepStatus } from "./cepLookup";
import {
  applyDocumentLang,
  LANGS,
  type Lang,
  readStoredLang,
  writeStoredLang,
} from "./i18n/lang";
import {
  COUNTRY_GROUPS,
  defaultCountry,
  regionProfile,
  submitStreetNumber,
} from "./signupRegions";
import "./landing.css";

type ProfileForm = {
  full_name: string;
  phone: string;
  country: string;
  postal_code: string;
  street: string;
  number: string;
  complement: string;
  district: string;
  city: string;
  state: string;
};

const COPY: Record<
  Lang,
  {
    title: string;
    lead: string;
    accountSection: string;
    addressSection: string;
    email: string;
    emailHint: string;
    fullName: string;
    phone: string;
    country: string;
    street: string;
    city: string;
    save: string;
    busy: string;
    saved: string;
    studio: string;
    logout: string;
    changePassword: string;
    loading: string;
    loadError: string;
    saveError: string;
    langAria: string;
    cepLooking: string;
    cepMiss: string;
    cepError: string;
    cepOk: string;
  }
> = {
  pt: {
    title: "Meu perfil",
    lead: "Atualize nome, telefone e endereço usados nos pedidos.",
    accountSection: "Seus dados",
    addressSection: "Endereço de entrega",
    email: "E-mail",
    emailHint: "O e-mail não pode ser alterado por aqui.",
    fullName: "Nome completo",
    phone: "Telefone / WhatsApp",
    country: "País",
    street: "Rua / avenida",
    city: "Cidade",
    save: "Salvar alterações",
    busy: "Salvando…",
    saved: "Dados atualizados.",
    studio: "Voltar ao estúdio",
    logout: "Sair",
    changePassword: "Alterar senha",
    loading: "Carregando…",
    loadError: "Não foi possível carregar seu perfil.",
    saveError: "Não foi possível salvar. Tente de novo.",
    langAria: "Idioma",
    cepLooking: "Buscando endereço…",
    cepMiss: "CEP não encontrado. Preencha o endereço.",
    cepError: "Não foi possível buscar o CEP. Preencha o endereço.",
    cepOk: "Endereço preenchido. Confira e informe o número.",
  },
  en: {
    title: "My profile",
    lead: "Update the name, phone, and address used for orders.",
    accountSection: "Your details",
    addressSection: "Shipping address",
    email: "Email",
    emailHint: "Email cannot be changed here.",
    fullName: "Full name",
    phone: "Phone / WhatsApp",
    country: "Country",
    street: "Street address",
    city: "City",
    save: "Save changes",
    busy: "Saving…",
    saved: "Profile updated.",
    studio: "Back to studio",
    logout: "Log out",
    changePassword: "Change password",
    loading: "Loading…",
    loadError: "Could not load your profile.",
    saveError: "Could not save. Please try again.",
    langAria: "Language",
    cepLooking: "Looking up address…",
    cepMiss: "ZIP not found. Enter the address manually.",
    cepError: "Could not look up the ZIP. Enter the address manually.",
    cepOk: "Address filled. Check it and add the number.",
  },
  es: {
    title: "Mi perfil",
    lead: "Actualiza nombre, teléfono y dirección usados en los pedidos.",
    accountSection: "Tus datos",
    addressSection: "Dirección de envío",
    email: "Correo",
    emailHint: "El correo no se puede cambiar aquí.",
    fullName: "Nombre completo",
    phone: "Teléfono / WhatsApp",
    country: "País",
    street: "Calle / avenida",
    city: "Ciudad",
    save: "Guardar cambios",
    busy: "Guardando…",
    saved: "Datos actualizados.",
    studio: "Volver al estudio",
    logout: "Salir",
    changePassword: "Cambiar contraseña",
    loading: "Cargando…",
    loadError: "No se pudo cargar tu perfil.",
    saveError: "No se pudo guardar. Inténtalo de nuevo.",
    langAria: "Idioma",
    cepLooking: "Buscando dirección…",
    cepMiss: "CEP no encontrado. Completa la dirección.",
    cepError: "No fue posible buscar el CEP. Completa la dirección.",
    cepOk: "Dirección rellenada. Revisa e indica el número.",
  },
};

function cepStatusText(status: CepStatus, t: (typeof COPY)[Lang]): string | null {
  if (status === "loading") return t.cepLooking;
  if (status === "ok") return t.cepOk;
  if (status === "miss") return t.cepMiss;
  if (status === "error") return t.cepError;
  return null;
}

function formFromMe(me: MeUser, lang: Lang): ProfileForm {
  return {
    full_name: me.full_name?.trim() || "",
    phone: me.phone?.trim() || "",
    country: (me.country?.trim() || defaultCountry(lang)).toUpperCase(),
    postal_code: me.postal_code?.trim() || "",
    street: me.street?.trim() || "",
    number: me.number?.trim() || "",
    complement: me.complement?.trim() || "",
    district: me.district?.trim() || "",
    city: me.city?.trim() || "",
    state: me.state?.trim() || "",
  };
}

function LangSwitch({
  lang,
  onChange,
  ariaLabel,
}: {
  lang: Lang;
  onChange: (lang: Lang) => void;
  ariaLabel: string;
}) {
  return (
    <div className="lang auth-lang" role="group" aria-label={ariaLabel} data-testid="conta-lang">
      {LANGS.map((code) => (
        <button
          key={code}
          type="button"
          className={lang === code ? "on" : ""}
          aria-pressed={lang === code}
          onClick={() => onChange(code)}
          data-testid={`conta-lang-${code}`}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

/**
 * Perfil do usuário autenticado: edita nome, telefone e endereço via PATCH /v1/auth/me.
 */
export function Conta() {
  const location = useLocation();
  const navigate = useNavigate();
  const [lang, setLangState] = useState<Lang>(() => readStoredLang("pt"));
  const t = COPY[lang];

  const [gate, setGate] = useState<"loading" | "ok" | "need-account">("loading");
  const [email, setEmail] = useState("");
  const [form, setForm] = useState<ProfileForm>(() => ({
    full_name: "",
    phone: "",
    country: defaultCountry(readStoredLang("pt")),
    postal_code: "",
    street: "",
    number: "",
    complement: "",
    district: "",
    city: "",
    state: "",
  }));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  const region = regionProfile(form.country);
  const isUsLayout = region.layout === "us";
  const cepStatus = useCepLookup(
    form.postal_code,
    gate === "ok" && form.country === "BR",
    (addr) => {
      setForm((prev) => ({
        ...prev,
        postal_code: addr.postal_code,
        street: addr.street || prev.street,
        district: addr.district || prev.district,
        city: addr.city || prev.city,
        state: addr.state || prev.state,
      }));
    },
  );

  useEffect(() => {
    document.title =
      lang === "en" ? "My profile — Story R Us" : lang === "es" ? "Mi perfil — Story R Us" : "Meu perfil — Story R Us";
  }, [lang]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!getToken()) {
        if (!cancelled) setGate("need-account");
        return;
      }
      try {
        const me = await api.me();
        if (cancelled) return;
        if (me.is_guest || !me.email_verified) {
          api.logout();
          setGate("need-account");
          return;
        }
        setEmail(me.email);
        setForm(formFromMe(me, lang));
        setGate("ok");
      } catch {
        api.logout();
        if (!cancelled) setGate("need-account");
      }
    })();
    return () => {
      cancelled = true;
    };
    // Só na montagem / troca de sessão; idioma inicial já veio do storage.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function setLang(nextLang: Lang) {
    setLangState(nextLang);
    writeStoredLang(nextLang);
    applyDocumentLang(nextLang);
  }

  function onCountryChange(country: string) {
    setForm((prev) => ({ ...prev, country, state: "" }));
  }

  function onPostalCodeChange(value: string) {
    setForm((prev) => ({
      ...prev,
      postal_code: prev.country === "BR" ? formatCep(value) : value,
    }));
  }

  function onLogout() {
    api.logout();
    navigate("/entrar", { replace: true });
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const payload: ProfileUpdatePayload = {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        postal_code: form.postal_code.trim(),
        street: form.street.trim(),
        number: submitStreetNumber(form.country, form.number),
        complement: form.complement.trim() || null,
        district: form.district.trim() || null,
        city: form.city.trim(),
        state: form.state.trim(),
        country: form.country.trim().toUpperCase(),
      };
      const updated = await api.updateMe(payload);
      setForm(formFromMe(updated, lang));
      setEmail(updated.email);
      setSaved(true);
    } catch (err) {
      const raw = ((err as Error).message || "").trim();
      setError(raw.replace(/^\d{3}:\s*/i, "").trim() || t.saveError);
    } finally {
      setBusy(false);
    }
  }

  if (gate === "loading") {
    return (
      <div className="kid auth-kid" data-testid="conta-page">
        <div className="auth-shell">
          <div className="auth-card">
            <p className="auth-lead" data-testid="conta-loading">
              {t.loading}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (gate === "need-account") {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={accountGateHref(next)} replace />;
  }

  const langSwitch = <LangSwitch lang={lang} onChange={setLang} ariaLabel={t.langAria} />;

  return (
    <div className="kid auth-kid auth-kid-full" data-testid="conta-page">
      <div className="auth-shell auth-shell-full">
        <div className="auth-card auth-card-full">
          <div className="auth-topbar">
            <Link to="/" className="auth-logo-inline">
              <img src={logo} alt="Story R Us" />
            </Link>
            {langSwitch}
          </div>
          <header className="auth-hero">
            <h1>{t.title}</h1>
            <p className="auth-lead">{t.lead}</p>
          </header>
          <form className="auth-form auth-form-full" onSubmit={onSubmit} data-testid="conta-form">
            <p className="auth-section-title auth-span-all">{t.accountSection}</p>
            <label className="auth-span-all">
              {t.fullName}
              <input
                type="text"
                required
                autoComplete="name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                data-testid="conta-full-name"
              />
            </label>
            <label>
              {t.email}
              <input
                type="email"
                readOnly
                disabled
                value={email}
                autoComplete="email"
                data-testid="conta-email"
              />
              <span className="auth-check-hint">{t.emailHint}</span>
            </label>
            <label>
              {t.phone}
              <input
                type="tel"
                required
                minLength={8}
                autoComplete="tel"
                placeholder={region.phonePlaceholder}
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                data-testid="conta-phone"
              />
            </label>

            <p className="auth-section-title auth-span-all">{t.addressSection}</p>
            <div
              className={`auth-address auth-span-all${isUsLayout ? " auth-address-us" : ""}`}
              data-testid="conta-address"
            >
              <label className="auth-span-all">
                {t.country}
                <select
                  required
                  value={form.country}
                  onChange={(e) => onCountryChange(e.target.value)}
                  data-testid="conta-country"
                  autoComplete="country"
                >
                  {COUNTRY_GROUPS.map((group) => (
                    <optgroup key={group.id} label={group.label[lang]}>
                      {group.countries.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.label[lang]}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </label>
              {isUsLayout ? (
                <>
                  <label className="auth-span-all">
                    {t.street}
                    <input
                      type="text"
                      required
                      autoComplete="street-address"
                      placeholder={region.streetPlaceholder[lang]}
                      value={form.street}
                      onChange={(e) => setForm({ ...form, street: e.target.value })}
                      data-testid="conta-street"
                    />
                  </label>
                  <label>
                    {region.numberLabel[lang]}
                    <input
                      type="text"
                      required={region.numberRequired}
                      placeholder={region.numberPlaceholder[lang]}
                      value={form.number}
                      onChange={(e) => setForm({ ...form, number: e.target.value })}
                      data-testid="conta-number"
                    />
                  </label>
                  <label>
                    {t.city}
                    <input
                      type="text"
                      required
                      autoComplete="address-level2"
                      value={form.city}
                      onChange={(e) => setForm({ ...form, city: e.target.value })}
                      data-testid="conta-city"
                    />
                  </label>
                  <label>
                    {region.stateLabel[lang]}
                    {region.stateOptions ? (
                      <select
                        required
                        value={form.state}
                        onChange={(e) => setForm({ ...form, state: e.target.value })}
                        data-testid="conta-state"
                        autoComplete="address-level1"
                      >
                        <option value="" disabled>
                          —
                        </option>
                        {region.stateOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        required
                        autoComplete="address-level1"
                        value={form.state}
                        onChange={(e) => setForm({ ...form, state: e.target.value })}
                        data-testid="conta-state"
                      />
                    )}
                  </label>
                  <label>
                    {region.postalLabel[lang]}
                    <input
                      type="text"
                      required
                      minLength={2}
                      maxLength={16}
                      autoComplete="postal-code"
                      placeholder={region.postalPlaceholder}
                      value={form.postal_code}
                      onChange={(e) => onPostalCodeChange(e.target.value)}
                      data-testid="conta-postal-code"
                    />
                  </label>
                </>
              ) : (
                <>
                  <label>
                    {region.postalLabel[lang]}
                    <input
                      type="text"
                      required
                      minLength={form.country === "BR" ? 8 : 2}
                      maxLength={form.country === "BR" ? 9 : 16}
                      inputMode={form.country === "BR" ? "numeric" : undefined}
                      autoComplete="postal-code"
                      placeholder={region.postalPlaceholder}
                      value={form.postal_code}
                      onChange={(e) => onPostalCodeChange(e.target.value)}
                      data-testid="conta-postal-code"
                    />
                    {form.country === "BR" && cepStatusText(cepStatus, t) && (
                      <span
                        className={`auth-cep-status is-${cepStatus}`}
                        data-testid="conta-cep-status"
                        role="status"
                      >
                        {cepStatusText(cepStatus, t)}
                      </span>
                    )}
                  </label>
                  <label>
                    {t.city}
                    <input
                      type="text"
                      required
                      autoComplete="address-level2"
                      value={form.city}
                      onChange={(e) => setForm({ ...form, city: e.target.value })}
                      data-testid="conta-city"
                    />
                  </label>
                  <label className="auth-span-all">
                    {t.street}
                    <input
                      type="text"
                      required
                      autoComplete="street-address"
                      placeholder={region.streetPlaceholder[lang]}
                      value={form.street}
                      onChange={(e) => setForm({ ...form, street: e.target.value })}
                      data-testid="conta-street"
                    />
                  </label>
                  <label>
                    {region.numberLabel[lang]}
                    <input
                      type="text"
                      required={region.numberRequired}
                      placeholder={region.numberPlaceholder[lang]}
                      value={form.number}
                      onChange={(e) => setForm({ ...form, number: e.target.value })}
                      data-testid="conta-number"
                    />
                  </label>
                  {region.showComplement && (
                    <label>
                      {region.complementLabel[lang]}
                      <input
                        type="text"
                        value={form.complement}
                        onChange={(e) => setForm({ ...form, complement: e.target.value })}
                        data-testid="conta-complement"
                      />
                    </label>
                  )}
                  {region.showDistrict && (
                    <label>
                      {region.districtLabel[lang]}
                      <input
                        type="text"
                        required={region.districtRequired}
                        value={form.district}
                        onChange={(e) => setForm({ ...form, district: e.target.value })}
                        data-testid="conta-district"
                      />
                    </label>
                  )}
                  <label>
                    {region.stateLabel[lang]}
                    {region.stateOptions ? (
                      <select
                        required
                        value={form.state}
                        onChange={(e) => setForm({ ...form, state: e.target.value })}
                        data-testid="conta-state"
                        autoComplete="address-level1"
                      >
                        <option value="" disabled>
                          —
                        </option>
                        {region.stateOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        required
                        minLength={1}
                        maxLength={80}
                        autoComplete="address-level1"
                        value={form.state}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            state:
                              form.country === "BR"
                                ? e.target.value.toUpperCase()
                                : e.target.value,
                          })
                        }
                        data-testid="conta-state"
                      />
                    )}
                  </label>
                </>
              )}
            </div>

            {error && (
              <p className="auth-error auth-span-all" role="alert" data-testid="conta-error">
                {error}
              </p>
            )}
            {saved && (
              <p className="auth-lead auth-span-all" role="status" data-testid="conta-saved">
                {t.saved}
              </p>
            )}
            <button
              type="submit"
              className="kbtn kbtn-primary auth-cta auth-span-all"
              disabled={busy}
              data-testid="conta-submit"
            >
              {busy ? t.busy : t.save}
            </button>
          </form>
          <p className="auth-foot">
            <Link to="/app" data-testid="conta-studio">
              {t.studio}
            </Link>
          </p>
          <p className="auth-foot">
            <Link
              to={`/esqueci-senha?next=${encodeURIComponent("/conta")}`}
              data-testid="conta-change-password"
            >
              {t.changePassword}
            </Link>
          </p>
          <p className="auth-foot">
            <button type="button" onClick={onLogout} data-testid="conta-logout">
              {t.logout}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
