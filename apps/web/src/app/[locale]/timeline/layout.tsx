import { Navigation } from "@/components/shared/Navigation";
import { DevModeBanner } from "@/components/shared/DevModeBanner";

interface LayoutProps {
  children: React.ReactNode;
  params: { locale: string };
}

export default function PageLayout({ children, params: { locale } }: LayoutProps) {
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
