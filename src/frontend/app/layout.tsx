import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import { Providers } from "@/components/Providers";
import TopNavigation from "@/components/TopNavigation";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Athena",
  description: "AI-powered trading platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className={`dark ${jetbrainsMono.variable}`}>
      <body className="flex h-screen flex-col bg-background">
        <Providers>
          <TopNavigation />
          <main className="flex-1 overflow-hidden">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
