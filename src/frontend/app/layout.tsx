import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Athena",
  description: "AI-powered trading platform",
};

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/market", label: "Market", icon: "📈" },
  { href: "/watchlist", label: "Watchlist", icon: "⭐" },
  { href: "/portfolio", label: "Portfolio", icon: "💼" },
  { href: "#", label: "Research", icon: "🔬", disabled: true },
  { href: "#", label: "Strategy", icon: "⚙️", disabled: true },
  { href: "#", label: "Backtest", icon: "⏪", disabled: true },
  { href: "#", label: "AI Center", icon: "🤖", disabled: true },
  { href: "#", label: "Settings", icon: "⚡", disabled: true },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="flex min-h-screen bg-gray-50">
        <aside className="w-56 border-r bg-white p-4">
          <div className="mb-8 text-xl font-bold text-gray-900">Athena</div>
          <nav className="space-y-1">
            {navItems.map((item) =>
              item.disabled ? (
                <span
                  key={item.label}
                  className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-400"
                >
                  <span>{item.icon}</span>
                  {item.label}
                </span>
              ) : (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <span>{item.icon}</span>
                  {item.label}
                </Link>
              )
            )}
          </nav>
        </aside>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
