"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
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

const schema = z.object({
  name: z.string().min(1, "Nome é obrigatório"),
  email: z.string().min(1, "E-mail é obrigatório").email("E-mail inválido"),
  password: z.string().min(8, "Senha deve ter no mínimo 8 caracteres"),
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormData) {
    try {
      await api.post("/api/v1/auth/register", { name: data.name, email: data.email, password: data.password });
      const res = await signIn("credentials", { email: data.email, password: data.password, redirect: false });
      if (res?.error) {
        router.push("/login");
      } else {
        router.push("/");
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ?? "Erro ao criar conta.";
      setError("root", { message: typeof msg === "string" ? msg : JSON.stringify(msg) });
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md rounded-3xl animate-scale-in">
        <CardHeader className="text-center pb-2">
          <h1 className="text-2xl font-bold gradient-text mb-1">CalorIA</h1>
          <CardTitle className="text-base font-medium">Criar conta</CardTitle>
          <CardDescription>Comece seu diário alimentar hoje</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <CardContent className="space-y-4 pt-4">
            {errors.root && (
              <p className="text-sm text-destructive bg-destructive/8 border border-destructive/15 px-3 py-2 rounded-lg">
                {errors.root.message}
              </p>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Nome
              </Label>
              <Input
                id="name"
                placeholder="Seu nome"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-xs text-destructive mt-1">{errors.name.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                E-mail
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-destructive mt-1">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Senha
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Mínimo 8 caracteres"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3 pt-2">
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Criando conta..." : "Criar conta"}
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
