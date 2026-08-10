import { ScheduleProposalList } from "@/components/proposal/ScheduleProposalList";
import { useTranslations } from "next-intl";

export default function SchedulePage({ params: { locale } }: { params: { locale: string } }) {
  return (
    <div className="space-y-6">
      <ScheduleProposalList />
    </div>
  );
}
