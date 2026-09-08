import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { ProgressList } from "./Studio";
import type { Job } from "./types";
import { state } from "./test/server";

afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

function ebookJob(overrides: Partial<Job> = {}): Job {
  return {
    id: "job-1",
    project_id: "p1",
    type: "EBOOK",
    status: "RUNNING",
    provider: null,
    cost_credits: 1,
    attempts: 1,
    error: null,
    created_at: "2026-01-01T00:00:00Z",
    result: { progress: { stage: "pages", done: 4, total: 11 } },
    ...overrides,
  };
}

describe("ProgressList", () => {
  it("mostra Ilustrando 4/11 no job EBOOK em andamento", () => {
    render(<ProgressList jobs={[ebookJob()]} />);
    expect(screen.getByText("Ilustrando 4/11")).toBeInTheDocument();
  });
});

describe("Polling do estúdio", () => {
  it("não recria o interval a cada update de jobs", async () => {
    state.credits = 10;
    const spy = vi.spyOn(window, "setInterval");
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: /criar projeto/i }));
    await user.click(screen.getByRole("button", { name: /gerar história com ia/i }));
    expect(await screen.findByText("STORY")).toBeInTheDocument();

    await waitFor(
      () => expect(screen.getByText(/pagina 1: ola/i)).toBeInTheDocument(),
      { timeout: 9000 },
    );

    const pollTimers = spy.mock.calls.filter((c) => c[1] === 2500);
    expect(pollTimers.length).toBeLessThanOrEqual(2);
  }, 20000);
});
