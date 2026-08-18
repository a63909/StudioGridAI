import { Navigation } from "@/components/shared/Navigation";
import { DevModeBanner } from "@/components/shared/DevModeBanner";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}

export default async function PageLayout({ children, params }: LayoutProps) {
  const { locale } = await params;
  return (
    <div className="min-h-screen flex flex-col">
      <DevModeBanner />
      <Navigation locale={locale} />
      <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6">
        {children}
      </main>
    </div>
  );
}
