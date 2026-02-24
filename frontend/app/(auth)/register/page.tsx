"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signIn } from "next-auth/react";
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
import api from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.post("/api/v1/auth/register", { name, email, password });
      const res = await signIn("credentials", { email, password, redirect: false });
      if (res?.error) {
        router.push("/login");
      } else {
        router.push("/");
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Erro ao criar conta.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-sm animate-fade-in">
        <CardHeader className="text-center pb-2">
          <h1 className="text-2xl font-bold gradient-text mb-1">CalorIA</h1>
          <CardTitle className="text-base font-medium">Criar conta</CardTitle>
          <CardDescription>Comece seu diário alimentar hoje</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-4">
            {error && (
              <p className="text-sm text-destructive bg-destructive/8 border border-destructive/15 px-3 py-2 rounded-lg">
                {error}
              </p>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Nome
              </Label>
              <Input
                id="name"
                placeholder="Seu nome"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
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
                placeholder="Mínimo 8 caracteres"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3 pt-2">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Criando conta..." : "Criar conta"}
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              Já tem conta?{" "}
              <Link href="/login" className="text-primary font-medium hover:underline">
                Entrar
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
