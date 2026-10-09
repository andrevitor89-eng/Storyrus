import type { Job } from "../types";

const CHAIN = ["AVATAR", "STORY", "EBOOK"] as const;

export type PreviewStepId = (typeof CHAIN)[number];
export type PreviewStepState = "wait" | "now" | "done";

export type PreviewStep = {
  id: PreviewStepId;
  state: PreviewStepState;
};

function isChainJob(job: Job): boolean {
  return (
    (job.type === "AVATAR" || job.type === "STORY" || job.type === "EBOOK") &&
    Boolean(job.result?.payload?.preview_chain)
  );
}

/** Etapas da prévia, na ordem em que o Studio as monta. */
export function previewChainSteps(jobs: Job[]): PreviewStep[] {
  const chain = jobs.filter(isChainJob);
  const latest = (type: PreviewStepId) => [...chain].reverse().find((job) => job.type === type);
  const states: PreviewStepState[] = CHAIN.map((type) => {
    const job = latest(type);
    if (job?.status === "DONE") return "done";
    if (job && (job.status === "PENDING" || job.status === "RUNNING")) return "now";
    return "wait";
  });

  for (let i = 0; i < states.length; i += 1) {
    if (states[i] === "wait" && states.slice(i + 1).some((state) => state !== "wait")) {
      states[i] = "done";
    }
  }

  if (states.every((state) => state === "wait")) states[0] = "now";

  return CHAIN.map((id, index) => ({ id, state: states[index] }));
}
