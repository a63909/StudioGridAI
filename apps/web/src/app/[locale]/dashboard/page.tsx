import { DashboardClient } from "@/components/dashboard/DashboardClient";
import { ProductionCommandCard } from "@/components/dashboard/ProductionCommandCard";

export default function DashboardPage() {
  return (
    <>
      <ProductionCommandCard />
      <DashboardClient />
    </>
  );
}
