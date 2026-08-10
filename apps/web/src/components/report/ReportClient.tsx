"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { WrapReport } from "@/lib/types/domain";
import { apiClient } from "@/lib/api/client";

export function ReportClient() {
  const t = useTranslations("report");
  const tc = useTranslations("common");
  const [report, setReport] = useState<WrapReport | null>(null);
  const [notWrapped, setNotWrapped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [wrapping, setWrapping] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const load = async () => {
    try {
      const data = await apiClient.getWrapReport();
      if ("status" in data) {
        setNotWrapped(true);
      } else {
        setReport(data as WrapReport);
        setNotWrapped(false);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleWrap = async () => {
    setWrapping(true);
    try {
      const r = await apiClient.wrapDay("production_manager");
      setReport(r);
      setNotWrapped(false);
      setConfirming(false);
    } finally {
      setWrapping(false);
    }
  };

  if (loading) return <div className="text-neutral-400 text-sm">{tc("loading")}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">{t("title")}</h1>
        {notWrapped && !confirming && (
          <button className="btn-primary text-sm" onClick={() => setConfirming(true)}>
            {t("wrap")}
          </button>
        )}
        {confirming && (
          <div className="flex items-center gap-3">
            <span className="text-yellow-300 text-sm">{t("wrapConfirm")}</span>
            <button
              className="btn-danger text-sm"
              onClick={handleWrap}
              disabled={wrapping}
            >
              {wrapping ? "..." : tc("confirm")}
            </button>
            <button className="btn-ghost text-sm" onClick={() => setConfirming(false)}>
              {tc("cancel")}
            </button>
          </div>
        )}
      </div>

      {notWrapped && !report && (
        <div className="card text-neutral-500 text-sm">{t("notGenerated")}</div>
      )}

      {report && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <ReportStat label={t("plannedShots")} value={report.plannedShotCount} />
          <ReportStat
            label={t("completedShots")}
            value={report.completedShotCount}
            variant={report.completedShotCount === report.plannedShotCount ? "success" : "warning"}
          />
          <ReportStat label={t("failedShots")} value={report.failedShotCount} variant={report.failedShotCount > 0 ? "danger" : "default"} />
          <ReportStat label={t("skippedShots")} value={report.skippedShotCount} />
          <ReportStat label={t("plannedScenes")} value={report.plannedSceneCount} />
          <ReportStat label={t("completedScenes")} value={report.completedSceneCount} variant="success" />
          <ReportStat label={t("totalDelay")} value={`${report.totalDelayMinutes} min`} variant={report.totalDelayMinutes > 0 ? "warning" : "default"} />
          <ReportStat label={t("recovered")} value={`${report.estimatedMinutesRecovered} min`} variant={report.estimatedMinutesRecovered > 0 ? "success" : "default"} />
          <ReportStat label={t("openRisks")} value={report.activeRiskIds.length} variant={report.activeRiskIds.length > 0 ? "warning" : "default"} />
          <ReportStat label={t("continuityIssues")} value={report.openContinuityAlerts.length} />
          <ReportStat label={t("coverageIssues")} value={report.openCoverageAlerts.length} />
        </div>
      )}
    </div>
  );
}

function ReportStat({
  label,
  value,
  variant = "default",
}: {
  label: string;
  value: string | number;
  variant?: "default" | "warning" | "danger" | "success";
}) {
  const valueClass = {
    default: "text-white",
    warning: "text-yellow-400",
    danger: "text-red-400",
    success: "text-green-400",
  }[variant];

  return (
    <div className="card">
      <div className={`text-2xl font-bold font-mono ${valueClass}`}>{value}</div>
      <div className="text-neutral-400 text-xs mt-1">{label}</div>
    </div>
  );
}
