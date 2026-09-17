import { useEffect, useRef, type Dispatch, type SetStateAction } from "react";
import { api } from "../api";
import type { Job, Project } from "../types";
import { mergeStudioAssets, type StudioAssets } from "./assets";

type Args = {
  project: Project | null;
  jobs: Job[];
  setProject: Dispatch<SetStateAction<Project | null>>;
  setJobs: Dispatch<SetStateAction<Job[]>>;
  setAssets: Dispatch<SetStateAction<StudioAssets | null>>;
  refreshCredits: () => void;
  isDemo: boolean;
};

/** Polls project/jobs/assets while an active job exists (interval 2500ms). */
export function useStudioPolling({
  project,
  jobs,
  setProject,
  setJobs,
  setAssets,
  refreshCredits,
  isDemo,
}: Args) {
  const pollRef = useRef<number | null>(null);
  const pollInFlightRef = useRef(false);
  const hasActiveJob = jobs.some((j) => j.status === "PENDING" || j.status === "RUNNING");

  useEffect(() => {
    if (!project || isDemo) return;
    const projectId = project.id;

    const tick = async () => {
      if (pollInFlightRef.current) return;
      pollInFlightRef.current = true;
      try {
        const js = await api.listJobs(projectId);
        const p = await api.getProject(projectId);
        setProject(p);
        setJobs(js);
        const stillActive = js.some((j) => j.status === "PENDING" || j.status === "RUNNING");
        api
          .getAssets(projectId)
          .then((next) => {
            setAssets((prev) => (stillActive ? mergeStudioAssets(prev, next) : next));
          })
          .catch(() => {});
        refreshCredits();
      } catch {
        /* ignore */
      } finally {
        pollInFlightRef.current = false;
      }
    };

    if (!hasActiveJob) {
      if (pollRef.current) window.clearInterval(pollRef.current);
      pollRef.current = null;
      api.getAssets(projectId).then(setAssets).catch(() => {});
      return;
    }

    void tick();
    pollRef.current = window.setInterval(() => {
      void tick();
    }, 2500);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
      pollRef.current = null;
    };
    // Deps match the former inline effect (project identity via project?.id).
  }, [project?.id, hasActiveJob, refreshCredits, isDemo]);
}
