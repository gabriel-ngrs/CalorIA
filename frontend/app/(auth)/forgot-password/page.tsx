"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";

const schema = z.object({
  email: z.string().min(1, "E-mail é obrigatório").email("E-mail inválido"),
});

type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormData) {
    try {
      await api.post("/api/v1/auth/forgot-password", { email: data.email });
    } catch {
      // Resposta uniforme: não revelamos se o e-mail existe, então tratamos
      // sucesso e erro da mesma forma para o usuário.
    }
    setSent(true);
  }

  return (
    <div className="w-full max-w-sm">
      <div className="mb-8">
        <h2 className="text-[1.6rem] font-bold tracking-tight">Recuperar senha</h2>
        <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
          Informe o e-mail da sua conta e enviaremos um link para redefinir a senha
        </p>
      </div>

      {sent ? (
        <div className="space-y-6">
          <div className="text-sm text-foreground bg-primary/8 border border-primary/20 px-4 py-3 rounded-xl leading-relaxed">
            Se o e-mail estiver cadastrado, enviamos um link de recuperação. Verifique
            sua caixa de entrada e o spam.
          </div>
          <p className="text-sm text-muted-foreground text-center">
            <Link href="/login" className="text-primary font-semibold hover:underline underline-offset-4">
              Voltar para o login
            </Link>
          </p>
        </div>
      ) : (
        <>
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                className="h-11 bg-background"
                {...register("email")}
              />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>

            <Button type="submit" className="w-full h-11 text-sm font-semibold mt-2" disabled={isSubmitting}>
              {isSubmitting ? "Enviando..." : "Enviar link de recuperação"}
            </Button>
          </form>

          <p className="text-sm text-muted-foreground text-center mt-6">
            Lembrou a senha?{" "}
            <Link href="/login" className="text-primary font-semibold hover:underline underline-offset-4">
              Entrar
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
