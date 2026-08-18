"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";

interface NavProps {
  locale: string;
}

export function Navigation({ locale }: NavProps) {
  const t = useTranslations("cloudDemo");

  return (
    <nav className="sticky top-0 z-20 border-b border-neutral-800 bg-neutral-950/95 backdrop-blur">
      <div className="max-w-screen-xl mx-auto px-4 flex items-center justify-between h-14">
        <Link href={`/${locale}/dashboard`} className="flex items-center gap-3">
          <span className="text-blue-400 font-bold text-sm tracking-widest">
            STUDIOGRID<span className="text-neutral-500"> AI</span>
          </span>
          <span className="hidden rounded-full border border-neutral-800 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-500 sm:inline">{t("nav")}</span>
        </Link>
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
