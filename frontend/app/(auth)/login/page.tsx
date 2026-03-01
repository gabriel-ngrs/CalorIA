"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
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

const DarkVeil = dynamic(() => import("@/components/auth/DarkVeil"), { ssr: false });

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

    if (res?.ok) {
      router.push("/");
    } else {
      setError("E-mail ou senha inválidos.");
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <DarkVeil
          hueShift={-24}
          speed={0.2}
          noiseIntensity={0.02}
          scanlineIntensity={0.05}
          scanlineFrequency={1.6}
          warpAmount={0.4}
        />
      </div>

      <div
        className="
          pointer-events-none absolute inset-0
          bg-[radial-gradient(ellipse_80%_65%_at_10%_0%,hsl(var(--primary)/0.35),transparent_58%),radial-gradient(ellipse_70%_55%_at_90%_100%,hsl(var(--accent)/0.22),transparent_55%),linear-gradient(to_bottom,hsl(var(--background)/0.28),hsl(var(--background)/0.82))]
        "
      />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-8">
        <Card className="w-full max-w-sm border-border/60 bg-card/90 shadow-xl backdrop-blur-sm animate-fade-in">
          <CardHeader className="text-center pb-2">
            <h1 className="text-2xl font-bold gradient-text mb-1">CalorIA</h1>
            <CardTitle className="text-base font-medium">Bem-vindo de volta</CardTitle>
            <CardDescription>Entre na sua conta para continuar</CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4 pt-4">
              {error && (
                <p className="text-sm text-destructive bg-destructive/8 border border-destructive/15 px-3 py-2 rounded-lg">
                  {error}
                </p>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
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
                <Label htmlFor="password" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
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
                <Link href="/register" className="text-primary font-medium hover:underline">
                  Cadastre-se
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
