"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { register, setToken } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await register(username, email, password, displayName);
      setToken(result.accessToken);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "注册失败");
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary";

  return (
    <div className="flex h-full items-center justify-center">
      <div className="panel w-full max-w-sm p-8">
        <h1 className="mb-6 text-center text-2xl font-bold text-foreground">注册 Athena</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="用户名" required className={inputClass} />
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="邮箱" required className={inputClass} />
          <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="显示名称（选填）" className={inputClass} />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="密码" required className={inputClass} />
          {error && <div className="text-xs text-destructive">{error}</div>}
          <button type="submit" disabled={loading} className="w-full rounded-lg bg-primary py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {loading ? "注册中..." : "注册"}
          </button>
        </form>
        <div className="mt-4 text-center text-sm text-muted-foreground">
          已有账号？
          <a href="/login" className="ml-1 text-primary hover:underline">登录</a>
        </div>
      </div>
    </div>
  );
}
