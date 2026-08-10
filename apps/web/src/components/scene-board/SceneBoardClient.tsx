"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { Scene } from "@/lib/types/domain";
import { apiClient } from "@/lib/api/client";

const STATUS_CLASS: Record<string, string> = {
  PLANNED: "status-planned",
  READY: "status-ready",
  IN_PROGRESS: "status-in-progress",
  PARTIAL: "status-partial",
  COMPLETE: "status-complete",
  BLOCKED: "status-blocked",
};

export function SceneBoardClient() {
  const t = useTranslations("sceneBoard");
  const ts = useTranslations("status");
  const tc = useTranslations("common");
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.listScenes().then(setScenes).finally(() => setLoading(false));
    const interval = setInterval(
      () => apiClient.listScenes().then(setScenes),
      8000
    );
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-neutral-400 text-sm">{tc("loading")}</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">{t("title")}</h1>
      {scenes.length === 0 ? (
        <div className="text-neutral-500 card">{t("noScenes")}</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenes.map((scene) => (
            <div
              key={scene.sceneId}
              className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-neutral-400 text-xs font-mono">
                  {t("scene")} {scene.sceneNumber}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded font-medium ${
                    STATUS_CLASS[scene.status] || "status-planned"
                  }`}
                >
                  {ts(scene.status.toLowerCase().replace("_", "") as any)}
                </span>
              </div>
              <div className="text-white font-medium">{scene.title}</div>
              <div className="text-neutral-400 text-sm">{scene.description.slice(0, 100)}...</div>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="bg-neutral-800 px-2 py-0.5 rounded text-neutral-400">
                  {t("location")}: {scene.locationId}
                </span>
                <span className="bg-neutral-800 px-2 py-0.5 rounded text-neutral-400">
                  {t("characters")}: {scene.characterIds.length}
                </span>
              </div>
              {scene.dependencies.length > 0 && (
                <div className="text-xs text-neutral-500">
                  {t("dependencies")}: {scene.dependencies.map((d) => d.dependsOnSceneId).join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
