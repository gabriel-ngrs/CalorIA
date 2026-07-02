"use client";

import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";

const schema = z.object({
  password: z.string().min(8, "Senha deve ter no mínimo 8 caracteres"),
});

type FormData = z.infer<typeof schema>;

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [done, setDone] = useState(false);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormData) {
    if (!token) {
      setError("root", { message: "Link inválido ou expirado. Solicite um novo." });
      return;
    }
    try {
      await api.post("/api/v1/auth/reset-password", {
        token,
        new_password: data.password,
      });
      setDone(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch {
      setError("root", {
        message: "Link inválido ou expirado. Solicite um novo link de recuperação.",
      });
    }
  }

  if (done) {
    return (
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <h2 className="text-[1.6rem] font-bold tracking-tight">Senha alterada</h2>
        </div>
        <div className="text-sm text-foreground bg-primary/8 border border-primary/20 px-4 py-3 rounded-xl leading-relaxed">
          Sua senha foi alterada com sucesso. Redirecionando para o login...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-sm">
      <div className="mb-8">
        <h2 className="text-[1.6rem] font-bold tracking-tight">Definir nova senha</h2>
        <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
          Escolha uma nova senha para a sua conta
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {errors.root && (
          <div className="text-sm text-destructive bg-destructive/8 border border-destructive/20 px-4 py-3 rounded-xl">
            {errors.root.message}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-sm font-medium">Nova senha</Label>
          <Input
            id="password"
            type="password"
            placeholder="Mínimo 8 caracteres"
            className="h-11 bg-background"
            {...register("password")}
          />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>

        <Button type="submit" className="w-full h-11 text-sm font-semibold mt-2" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : "Salvar nova senha"}
        </Button>
      </form>

      <p className="text-sm text-muted-foreground text-center mt-6">
        <Link href="/login" className="text-primary font-semibold hover:underline underline-offset-4">
          Voltar para o login
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="w-full max-w-sm" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
