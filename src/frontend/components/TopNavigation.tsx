"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import UserMenu from "@/components/UserMenu";

const ROUTES = [
  { href: "/dashboard", label: "大盘", key: "dashboard" },
  { href: "/watchlist", label: "自选", key: "watchlist" },
  { href: "/portfolio", label: "组合", key: "portfolio" },
  { href: "/strategy", label: "策略", key: "strategy" },
  { href: "/backtest", label: "回测", key: "backtest" },
];

function LiveClock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <span className="font-mono text-xs text-muted-foreground tabular-nums">
      {time.toLocaleTimeString("zh-CN", { hour12: false })}
    </span>
  );
}

export default function TopNavigation() {
  const pathname = usePathname();
  const [latency, setLatency] = useState(12);
  const [blink, setBlink] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => {
      setLatency(Math.floor(Math.random() * 20) + 5);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setBlink((b) => !b), 500);
    return () => clearInterval(timer);
  }, []);

  const activeKey = ROUTES.find((r) => pathname.startsWith(r.href))?.key ?? "dashboard";

  return (
    <nav className="flex h-10 items-center border-b border-divider bg-background/95 backdrop-blur-sm px-3 select-none shrink-0">
      <div className="flex items-center gap-2 mr-6">
        <Link href="/dashboard" className="flex items-center gap-1.5">
          <span className="text-xs font-bold tracking-widest text-primary">ATHENA</span>
        </Link>
      </div>

      <div className="flex items-center gap-0">
        {ROUTES.map((route) => (
          <Link
            key={route.key}
            href={route.href}
            className={cn(
              "relative px-3 py-2 text-xs font-medium transition-colors",
              activeKey === route.key
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground/80"
            )}
          >
            {route.label}
            {activeKey === route.key && (
              <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-3/4 h-0.5 bg-primary rounded-full" />
            )}
          </Link>
        ))}
      </div>

      <div className="ml-auto flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="text-[10px] font-medium text-emerald-400 tracking-wide">Paper</span>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className={cn("h-1.5 w-1.5 rounded-full", latency < 20 ? "bg-emerald-400" : latency < 50 ? "bg-amber-400" : "bg-down")} />
          <span className="font-mono tabular-nums">{latency}ms</span>
        </div>

        <LiveClock />

        <div className="pl-2 border-l border-divider">
          <UserMenu />
        </div>
      </div>
    </nav>
  );
}
