import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Group 3 · Marketplace Weekly Dashboard",
  description: "Interactive Brazilian e-commerce marketplace dashboard",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
