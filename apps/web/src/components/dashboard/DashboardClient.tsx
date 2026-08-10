"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { DashboardStats } from "@/lib/types/domain";
import { apiClient } from "@/lib/api/client";

interface StatCardProps {
  label: string;
  value: string | number;
  variant?: "default" | "warning" | "danger" | "success";
}

function StatCard({ label, value, variant = "default" }: StatCardProps) {
  const variantClass = {
    default: "border-neutral-800",
    warning: "border-yellow-800",
    danger: "border-red-800",
    success: "border-green-800",
  }[variant];

  const valueClass = {
    default: "text-white",
    warning: "text-yellow-400",
    danger: "text-red-400",
    success: "text-green-400",
  }[variant];

  return (
    <div className={`bg-neutral-900 border ${variantClass} rounded-lg p-4`}>
      <div className={`text-2xl font-bold font-mono ${valueClass}`}>{value}</div>
      <div className="text-neutral-400 text-xs mt-1">{label}</div>
    </div>
  );
}

export function DashboardClient({ locale }: { locale: string }) {
  const t = useTranslations("dashboard");
  const tc = useTranslations("common");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.getDashboardStats();
        setStats(data);
      } catch {
        setError("An error occurred");
      } finally {
        setLoading(false);
      }
    }
    load();
    // Refresh every 10 seconds
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return <div className="text-neutral-400 text-sm">{tc("loading")}</div>;
  }

  if (error || !stats) {
    return <div className="text-red-400 text-sm">{error || tc("noData")}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">{t("title")}</h1>
        <div className="text-xs text-neutral-500 font-mono">{stats.shootDayId}</div>
      </div>

      {/* Stats grid — all values from API, never hardcoded */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <StatCard label={t("scenesPlanned")} value={stats.plannedSceneCount} />
        <StatCard
          label={t("scenesCompleted")}
          value={stats.completedSceneCount}
          variant={stats.completedSceneCount === stats.plannedSceneCount ? "success" : "default"}
        />
        <StatCard label={t("shotsPlanned")} value={stats.plannedShotCount} />
        <StatCard
          label={t("shotsCompleted")}
          value={stats.completedShotCount}
          variant={stats.completedShotCount === stats.plannedShotCount ? "success" : "default"}
        />
        <StatCard
          label={t("atRisk")}
          value={stats.atRiskCount}
          variant={stats.atRiskCount > 0 ? "warning" : "default"}
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label={t("continuityAlerts")}
          value={stats.openContinuityAlerts}
          variant={stats.openContinuityAlerts > 0 ? "warning" : "default"}
        />
        <StatCard
          label={t("coverageAlerts")}
          value={stats.openCoverageAlerts}
          variant={stats.openCoverageAlerts > 0 ? "warning" : "default"}
        />
        <StatCard
          label={t("scheduleDelay")}
          value={`${stats.totalDelayMinutes} min`}
          variant={stats.totalDelayMinutes > 0 ? "warning" : "default"}
        />
        <StatCard
          label={t("estimatedRecovered")}
          value={`${stats.estimatedMinutesRecovered} min`}
          variant={stats.estimatedMinutesRecovered > 0 ? "success" : "default"}
        />
      </div>

      {stats.pendingProposals > 0 && (
        <div className="bg-blue-950 border border-blue-800 rounded-lg p-4">
          <div className="text-blue-300 font-medium text-sm">
            {t("activeProposals")}: {stats.pendingProposals}
          </div>
          <a
            href={`/${locale}/schedule`}
            className="text-blue-400 hover:text-blue-300 text-xs mt-1 underline inline-block"
          >
            → Review proposals
          </a>
        </div>
      )}
    </div>
  );
}
