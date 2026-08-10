"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { key: "dashboard", href: "dashboard" },
  { key: "timeline", href: "timeline" },
  { key: "sceneBoard", href: "scene-board" },
  { key: "coverage", href: "coverage" },
  { key: "continuity", href: "continuity" },
  { key: "schedule", href: "schedule" },
  { key: "report", href: "report" },
] as const;

interface NavProps {
  locale: string;
}

export function Navigation({ locale }: NavProps) {
  const t = useTranslations("nav");
  const pathname = usePathname();

  return (
    <nav className="bg-neutral-900 border-b border-neutral-800">
      <div className="max-w-screen-xl mx-auto px-4 flex items-center justify-between h-12">
        <div className="flex items-center gap-1">
          <span className="text-blue-400 font-bold mr-4 text-sm tracking-widest">
            STUDIOGRID<span className="text-neutral-500"> AI</span>
          </span>
          <div className="flex gap-1 overflow-x-auto">
            {NAV_ITEMS.map((item) => {
              const href = `/${locale}/${item.href}`;
              const isActive = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link
                  key={item.key}
                  href={href}
                  className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
                  }`}
                >
                  {t(item.key)}
                </Link>
              );
            })}
          </div>
        </div>
        <LanguageSwitcher locale={locale} />
      </div>
    </nav>
  );
}

function LanguageSwitcher({ locale }: { locale: string }) {
  const t = useTranslations("language");
  const pathname = usePathname();

  const switchLocale = (newLocale: string) => {
    // Replace locale segment in pathname
    const segments = pathname.split("/");
    segments[1] = newLocale;
    return segments.join("/");
  };

  return (
    <div className="flex gap-1 text-xs">
      {["en", "ru"].map((lang) => (
        <Link
          key={lang}
          href={switchLocale(lang)}
          className={`px-2 py-1 rounded transition-colors ${
            locale === lang
              ? "bg-neutral-700 text-white font-semibold"
              : "text-neutral-500 hover:text-neutral-300"
          }`}
          aria-label={t("switchTo")}
        >
          {lang.toUpperCase()}
        </Link>
      ))}
    </div>
  );
}
