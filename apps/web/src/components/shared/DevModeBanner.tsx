"use client";

import { useTranslations } from "next-intl";
import { AIRuntimeStatus } from "./AIRuntimeStatus";

/**
 * Runtime banner — shows AI status.
 * DEV MODE: when STUDIOGRID_AI_ENABLED=0
 * Shows real AI Runtime status when enabled.
 */
export function DevModeBanner() {
  const t = useTranslations("devMode");

  return (
    <div className="runtime-banner px-4 py-2 flex items-center justify-between text-sm">
      <div className="flex items-center gap-3">
        <span className="font-mono font-bold text-blue-300 tracking-wide">
          {t("banner")}
        </span>
        <span className="text-neutral-400 hidden sm:inline">{t("description")}</span>
      </div>
      <div className="flex items-center gap-4 text-xs">
        <AIRuntimeStatus />
        <span className="text-orange-400">
          {t("partnerStatus")}: <span className="font-mono font-semibold">NOT_CONFIGURED</span>
        </span>
      </div>
    </div>
  );
}
