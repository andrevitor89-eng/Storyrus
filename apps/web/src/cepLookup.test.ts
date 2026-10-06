import { afterEach, describe, expect, it, vi } from "vitest";
import { digitsCep, formatCep, lookupCep, viaCepUrl } from "./cepLookup";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("cepLookup", () => {
  it("normaliza e formata CEP", () => {
    expect(digitsCep("01310-100")).toBe("01310100");
    expect(digitsCep("01310 100 extra")).toBe("01310100");
    expect(formatCep("01310100")).toBe("01310-100");
    expect(formatCep("01310")).toBe("01310");
    expect(viaCepUrl("01310-100")).toBe("https://viacep.com.br/ws/01310100/json/");
  });

  it("preenche rua, bairro, cidade e UF", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        cep: "01310-100",
        logradouro: "Avenida Paulista",
        bairro: "Bela Vista",
        localidade: "São Paulo",
        uf: "SP",
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const addr = await lookupCep("01310-100");
    expect(addr).toEqual({
      postal_code: "01310-100",
      street: "Avenida Paulista",
      district: "Bela Vista",
      city: "São Paulo",
      state: "SP",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://viacep.com.br/ws/01310100/json/",
      expect.objectContaining({ signal: undefined }),
    );
  });

  it("devolve null quando o CEP não existe", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ erro: true }),
      })),
    );
    expect(await lookupCep("00000000")).toBeNull();
  });

  it("não chama a API com CEP incompleto", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    expect(await lookupCep("01310")).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
