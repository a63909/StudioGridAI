import { Navigation } from "@/components/shared/Navigation";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}

export default async function LocaleLayout({ children, params }: LayoutProps) {
  const { locale } = await params;
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation locale={locale} />
      <main className="flex-1 w-full">
        {children}
      </main>
    </div>
  );
}
