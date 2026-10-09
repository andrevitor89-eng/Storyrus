import { describe, expect, it } from "vitest";
import type { Job } from "../types";
import { previewChainSteps } from "./previewSteps";

function job(type: Job["type"], status: Job["status"]): Job {
  return {
    id: `${type}-${status}`,
    project_id: "p1",
    type,
    status,
    provider: null,
    cost_credits: 1,
    attempts: 1,
    error: null,
    created_at: "2026-01-01T00:00:00Z",
    result: { payload: { preview_chain: true } },
  };
}

describe("previewChainSteps", () => {
  it("começa no personagem quando ainda não há jobs", () => {
    expect(previewChainSteps([]).map((step) => step.state)).toEqual(["now", "wait", "wait"]);
  });

  it("marca a etapa em andamento e as anteriores como prontas", () => {
    const steps = previewChainSteps([
      job("AVATAR", "DONE"),
      job("STORY", "DONE"),
      job("EBOOK", "RUNNING"),
    ]);
    expect(steps.map((step) => [step.id, step.state])).toEqual([
      ["AVATAR", "done"],
      ["STORY", "done"],
      ["EBOOK", "now"],
    ]);
  });

  it("trata etapa anterior ausente como pronta se a seguinte já começou", () => {
    expect(previewChainSteps([job("EBOOK", "PENDING")]).map((step) => step.state)).toEqual([
      "done",
      "done",
      "now",
    ]);
  });
});
