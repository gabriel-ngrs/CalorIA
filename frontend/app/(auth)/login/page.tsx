"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Sparkles } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    setLoading(false);

    if (res?.error) {
      setError("E-mail ou senha inválidos.");
    } else {
      router.push("/");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Orbes decorativos de fundo */}
      <div
        className="absolute top-1/4 -left-32 w-80 h-80 rounded-full opacity-20 animate-float"
        style={{
          background: "radial-gradient(circle, hsl(var(--primary)) 0%, transparent 70%)",
          filter: "blur(40px)",
        }}
      />
      <div
        className="absolute bottom-1/4 -right-24 w-64 h-64 rounded-full opacity-15 animate-float"
        style={{
          background: "radial-gradient(circle, hsl(var(--accent)) 0%, transparent 70%)",
          filter: "blur(40px)",
          animationDelay: "2s",
        }}
      />

      <Card className="w-full max-w-sm animate-scale-in">
        <CardHeader className="text-center pb-2">
          <div className="flex items-center justify-center gap-2 mb-1">
            <div className="h-9 w-9 rounded-xl glass-card flex items-center justify-center glow-primary-sm">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
          </div>
          <CardTitle className="text-3xl gradient-text font-bold">CalorIA</CardTitle>
          <CardDescription>Entre na sua conta</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-4">
            {error && (
              <p className="text-sm text-destructive glass border border-destructive/20 px-3 py-2 rounded-xl">
                {error}
              </p>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-foreground/80 text-xs font-medium uppercase tracking-wide">
                E-mail
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-foreground/80 text-xs font-medium uppercase tracking-wide">
                Senha
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3 pt-2">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              Não tem conta?{" "}
              <Link href="/register" className="text-primary hover:text-primary/80 font-medium transition-colors">
                Cadastre-se
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
