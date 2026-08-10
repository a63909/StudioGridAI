import { useTranslations } from "next-intl";
import { DashboardClient } from "@/components/dashboard/DashboardClient";

export default function DashboardPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  return <DashboardClient locale={locale} />;
}
