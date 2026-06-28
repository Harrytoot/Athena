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
        className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-destructive"
      >
        <LogOut className="h-4 w-4" />
        退出
      </button>
    );
  }

  return (
    <Link
      href="/login"
      className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-primary"
    >
      <User className="h-4 w-4" />
      登录
    </Link>
  );
}
