"use client";

import Link from "next/link";
import { LogOut, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

export default function UserMenu() {
  const { loggedIn, logout } = useAuth();

  if (loggedIn) {
    return (
      <button
        onClick={logout}
        className="flex items-center gap-1 text-[11px] text-muted-foreground transition-colors hover:text-destructive"
      >
        <LogOut className="h-3.5 w-3.5" />
        退出
      </button>
    );
  }

  return (
    <Link
      href="/login"
      className="flex items-center gap-1 text-[11px] text-muted-foreground transition-colors hover:text-primary"
    >
      <User className="h-3.5 w-3.5" />
      登录
    </Link>
  );
}
