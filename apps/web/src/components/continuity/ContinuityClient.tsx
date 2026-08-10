"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { ContinuityAlert, ContinuityFact } from "@/lib/types/domain";
import { apiClient } from "@/lib/api/client";

export function ContinuityClient() {
  const t = useTranslations("continuity");
  const tc = useTranslations("common");
  const tat = useTranslations("alertType");
  const [facts, setFacts] = useState<ContinuityFact[]>([]);
  const [alerts, setAlerts] = useState<ContinuityAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const [f, a] = await Promise.all([
      apiClient.listContinuityFacts(),
      apiClient.listContinuityAlerts(),
    ]);
    setFacts(f);
    setAlerts(a);
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (alertId: string, override = false) => {
    await apiClient.resolveAlert(alertId, {
      resolution: "Reviewed and resolved by script supervisor",
      resolvedBy: "script_supervisor",
      override,
    });
    await load();
  };

  if (loading) return <div className="text-neutral-400 text-sm">{tc("loading")}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">{t("title")}</h1>

      {/* Alerts */}
      <section>
        <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">
          {t("alerts")}
        </h2>
        {alerts.length === 0 ? (
          <div className="card text-neutral-500 text-sm">{t("noAlerts")}</div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.alertId}
                className={`bg-neutral-900 border rounded-lg p-4 space-y-3 ${
                  alert.status === "OPEN"
                    ? "border-yellow-800"
                    : "border-neutral-800 opacity-70"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="alert-type-inference text-xs px-2 py-0.5 rounded font-mono">
                    {tat(alert.alertType.toLowerCase() as "inference")}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      alert.status === "OPEN"
                        ? "bg-yellow-950 text-yellow-400"
                        : "bg-neutral-800 text-neutral-400"
                    }`}
                  >
                    {alert.status}
                  </span>
                </div>
                <p className="text-neutral-200 text-sm">{alert.description}</p>
                {alert.alertType === "INFERENCE" && (
                  <p className="text-yellow-500 text-xs italic">{t("inferenceNote")}</p>
                )}
                <div className="bg-neutral-800 rounded p-3 text-xs space-y-1">
                  <div className="text-neutral-400">
                    <span className="text-neutral-300 font-medium">{t("scene")} A:</span>{" "}
                    {alert.factA.sceneId} — {alert.factA.attribute} = {alert.factA.value}
                  </div>
                  <div className="text-neutral-400">
                    <span className="text-neutral-300 font-medium">{t("scene")} B:</span>{" "}
                    {alert.factB.sceneId} — {alert.factB.attribute} = {alert.factB.value}
                  </div>
                </div>
                {alert.status === "OPEN" && (
                  <div className="flex gap-2">
                    <button
                      className="btn-ghost text-sm"
                      onClick={() => handleResolve(alert.alertId)}
                    >
                      {tc("resolve")}
                    </button>
                    <button
                      className="btn-danger text-sm"
                      onClick={() => handleResolve(alert.alertId, true)}
                    >
                      {tc("override")}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Facts */}
      <section>
        <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">
          {t("facts")}
        </h2>
        {facts.length === 0 ? (
          <div className="card text-neutral-500 text-sm">{t("noFacts")}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-neutral-500 text-xs border-b border-neutral-800">
                  <th className="pb-2 pr-4">{t("scene")}</th>
                  <th className="pb-2 pr-4">{t("shot")}</th>
                  <th className="pb-2 pr-4">{t("attribute")}</th>
                  <th className="pb-2 pr-4">{t("value")}</th>
                  <th className="pb-2">{t("source")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {facts.map((fact) => (
                  <tr key={fact.factId} className="text-neutral-300">
                    <td className="py-2 pr-4 font-mono text-xs">{fact.sceneId}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{fact.shotId ?? "—"}</td>
                    <td className="py-2 pr-4">{fact.attribute}</td>
                    <td className="py-2 pr-4 font-semibold">{fact.value}</td>
                    <td className="py-2 text-neutral-500 text-xs">{fact.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
