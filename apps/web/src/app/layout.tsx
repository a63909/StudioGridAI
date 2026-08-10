import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StudioGrid AI",
  description: "AI Production Control Room for Film Shoots",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
