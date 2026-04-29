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
    <div className="w-full max-w-sm">
      {/* Brand — só mobile */}
      <div className="lg:hidden text-center mb-10">
        <div className="inline-flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-base">🥗</div>
          <span className="text-2xl font-bold tracking-tight text-primary">CalorIA</span>
        </div>
        <p className="text-sm text-muted-foreground">Seu diário alimentar inteligente</p>
      </div>

      {/* Cabeçalho */}
      <div className="mb-8">
        <h2 className="text-[1.6rem] font-bold tracking-tight">Criar conta grátis</h2>
        <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
          Comece a entender o que você come em menos de 2 minutos
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {errors.root && (
          <div className="text-sm text-destructive bg-destructive/8 border border-destructive/20 px-4 py-3 rounded-xl">
            {errors.root.message}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="name" className="text-sm font-medium">Nome</Label>
          <Input id="name" placeholder="Seu nome" className="h-11 bg-background" {...register("name")} />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email" className="text-sm font-medium">E-mail</Label>
          <Input id="email" type="email" placeholder="seu@email.com" className="h-11 bg-background" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-sm font-medium">Senha</Label>
          <Input id="password" type="password" placeholder="Mínimo 8 caracteres" className="h-11 bg-background" {...register("password")} />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>

        <Button type="submit" className="w-full h-11 text-sm font-semibold mt-2" disabled={isSubmitting}>
          {isSubmitting ? "Criando conta..." : "Criar conta grátis"}
        </Button>
      </form>

      {/* Divisor */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-background px-3 text-xs text-muted-foreground">ou</span>
        </div>
      </div>

      <p className="text-sm text-muted-foreground text-center">
        Já tem conta?{" "}
        <Link href="/login" className="text-primary font-semibold hover:underline underline-offset-4">
          Entrar
        </Link>
      </p>
    </div>
  );
}

