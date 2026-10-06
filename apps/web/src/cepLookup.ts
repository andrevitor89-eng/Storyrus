import { useEffect, useRef, useState } from "react";

export type CepAddress = {
  postal_code: string;
  street: string;
  district: string;
  city: string;
  state: string;
};

export type CepStatus = "idle" | "loading" | "ok" | "miss" | "error";

export function digitsCep(raw: string): string {
  return raw.replace(/\D/g, "").slice(0, 8);
}

export function formatCep(raw: string): string {
  const digits = digitsCep(raw);
  if (digits.length <= 5) return digits;
  return `${digits.slice(0, 5)}-${digits.slice(5)}`;
}

export function viaCepUrl(cep: string): string {
  return `https://viacep.com.br/ws/${digitsCep(cep)}/json/`;
}

export async function lookupCep(
  raw: string,
  signal?: AbortSignal,
): Promise<CepAddress | null> {
  const cep = digitsCep(raw);
  if (cep.length !== 8) return null;
  const resp = await fetch(viaCepUrl(cep), { signal });
  if (!resp.ok) {
    throw new Error(`cep_http_${resp.status}`);
  }
  const data = (await resp.json()) as {
    erro?: boolean;
    logradouro?: string;
    bairro?: string;
    localidade?: string;
    uf?: string;
  };
  if (data?.erro) return null;
  return {
    postal_code: formatCep(cep),
    street: String(data.logradouro || "").trim(),
    district: String(data.bairro || "").trim(),
    city: String(data.localidade || "").trim(),
    state: String(data.uf || "").trim().toUpperCase(),
  };
}

/** Busca ViaCEP quando o CEP brasileiro chega a 8 dígitos. */
export function useCepLookup(
  postalCode: string,
  enabled: boolean,
  onAddress: (addr: CepAddress) => void,
): CepStatus {
  const [status, setStatus] = useState<CepStatus>("idle");
  const lastCep = useRef("");
  const onAddressRef = useRef(onAddress);
  onAddressRef.current = onAddress;

  useEffect(() => {
    if (!enabled) {
      lastCep.current = "";
      setStatus("idle");
      return;
    }
    const cep = digitsCep(postalCode);
    if (cep.length !== 8) {
      lastCep.current = "";
      setStatus("idle");
      return;
    }
    if (lastCep.current === cep) return;
    lastCep.current = cep;
    const ctrl = new AbortController();
    const timer = window.setTimeout(() => {
      setStatus("loading");
      void lookupCep(cep, ctrl.signal)
        .then((addr) => {
          if (ctrl.signal.aborted) return;
          if (!addr) {
            setStatus("miss");
            return;
          }
          onAddressRef.current(addr);
          setStatus("ok");
        })
        .catch((err: unknown) => {
          if ((err as { name?: string })?.name === "AbortError") return;
          setStatus("error");
        });
    }, 280);
    return () => {
      window.clearTimeout(timer);
      ctrl.abort();
    };
  }, [enabled, postalCode]);

  return status;
}
