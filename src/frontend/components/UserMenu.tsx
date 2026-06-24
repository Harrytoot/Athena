"use client";

import { clearToken, isLoggedIn } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

export default function UserMenu() {
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
  }, []);

  const handleLogout = useCallback(() => {
    clearToken();
    setLoggedIn(false);
    router.push("/login");
  }, [router]);

  if (loggedIn) {
    return (
      <button
        onClick={handleLogout}
        className="text-sm text-gray-500 hover:text-red-500"
      >
        退出
      </button>
    );
  }

  return (
    <Link href="/login" className="text-sm text-blue-600 hover:underline">
      登录
    </Link>
  );
}
