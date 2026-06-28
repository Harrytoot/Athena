import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import { Providers } from "@/components/Providers";
import UserMenu from "@/components/UserMenu";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Athena",
  description: "AI-powered trading platform",
};

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/market", label: "Market", icon: "📈" },
  { href: "/watchlist", label: "Watchlist", icon: "⭐" },
  { href: "/portfolio", label: "Portfolio", icon: "💼" },
  { href: "/recommendation", label: "Recommend", icon: "💡" },
  { href: "/strategy", label: "Strategy", icon: "⚙️" },
  { href: "/backtest", label: "Backtest", icon: "⏪" },
  { href: "#", label: "AI Center", icon: "🤖", disabled: true },
  { href: "#", label: "Settings", icon: "⚡", disabled: true },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className={`dark ${jetbrainsMono.variable}`}>
      <body className="flex h-screen bg-background">
        <Providers>
          <aside className="flex w-56 flex-shrink-0 flex-col border-r border-border bg-card">
            <div className="px-4 pt-4 pb-3">
              <div className="text-xl font-bold text-primary">Athena</div>
              <div className="mt-0.5 text-xs text-muted-foreground">
                量化交易终端
              </div>
            </div>
            <nav className="flex-1 space-y-0.5 px-2">
              {navItems.map((item) =>
                item.disabled ? (
                  <span
                    key={item.label}
                    className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground/40"
                  >
                    <span className="text-base">{item.icon}</span>
                    {item.label}
                  </span>
                ) : (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  >
                    <span className="text-base">{item.icon}</span>
                    {item.label}
                  </Link>
                )
              )}
            </nav>
            <div className="border-t border-border p-3">
              <UserMenu />
            </div>
          </aside>
          <main className="flex-1 overflow-hidden">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
