"use client";

import { useTranslations } from "next-intl";

/**
 * DEV MODE banner — always visible in Phase 1.
 * Clearly communicates that AI is not connected.
 * Must never be removed unless real Gemini inference is active.
 */
export function DevModeBanner() {
  const t = useTranslations("devMode");

  return (
    <div className="dev-mode-banner px-4 py-2 flex items-center justify-between text-sm">
      <div className="flex items-center gap-3">
        <span className="font-mono font-bold text-orange-300 tracking-wide">
          ⚠ {t("banner")}
        </span>
        <span className="text-orange-400 hidden sm:inline">{t("description")}</span>
      </div>
      <div className="flex items-center gap-4 text-orange-400 text-xs">
        <span>
          {t("partnerStatus")}: <span className="font-mono font-semibold">NOT_CONFIGURED</span>
        </span>
      </div>
    </div>
  );
}
