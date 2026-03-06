"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Check,
  CheckCircle2,
  Clock,
  Copy,
  MessageCircle,
  MessageSquare,
  RefreshCw,
  Send,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useGenerateTelegramToken, useGenerateWhatsAppToken, useMe } from "@/lib/hooks/useProfile";

function StepItem({ number, children }: { number: number; children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-3">
      <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/15 text-primary text-[11px] font-bold shrink-0 mt-0.5">
        {number}
      </span>
      <span className="text-sm text-muted-foreground leading-relaxed">{children}</span>
    </li>
  );
}

export default function ConectarPage() {
  const { data: user } = useMe();
  const generateTelegram = useGenerateTelegramToken();
  const generateWhatsApp = useGenerateWhatsAppToken();
  const [telegramToken, setTelegramToken] = useState<string | null>(null);
  const [whatsappToken, setWhatsappToken] = useState<string | null>(null);
  const [copied, setCopied] = useState<"telegram" | "whatsapp" | null>(null);

  async function copyToClipboard(text: string, channel: "telegram" | "whatsapp") {
    await navigator.clipboard.writeText(text);
    setCopied(channel);
    setTimeout(() => setCopied(null), 2000);
  }

  const telegramConnected = !!user?.telegram_chat_id;
  const whatsappConnected = !!user?.whatsapp_number;

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageCircle className="h-6 w-6 text-primary" />
          Conectar Bot
        </h1>
        <p className="text-muted-foreground text-sm">Vincule seus canais de mensagem</p>
      </div>

      {/* Status chips */}
      <div className="flex gap-3 flex-wrap">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${
          telegramConnected
            ? "border-blue-500/30 bg-blue-500/5 text-blue-400"
            : "border-muted/30 bg-muted/5 text-muted-foreground"
        }`}>
          {telegramConnected
            ? <Wifi className="h-3.5 w-3.5" />
            : <WifiOff className="h-3.5 w-3.5" />}
          <span className="font-medium">Telegram</span>
          <span className="text-xs opacity-70">{telegramConnected ? "conectado" : "não conectado"}</span>
        </div>
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${
          whatsappConnected
            ? "border-green-500/30 bg-green-500/5 text-green-400"
            : "border-muted/30 bg-muted/5 text-muted-foreground"
        }`}>
          {whatsappConnected
            ? <Wifi className="h-3.5 w-3.5" />
            : <WifiOff className="h-3.5 w-3.5" />}
          <span className="font-medium">WhatsApp</span>
          <span className="text-xs opacity-70">{whatsappConnected ? "conectado" : "não conectado"}</span>
        </div>
      </div>

      {/* Cards lado a lado */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Telegram */}
        <Card className={`transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl ${
          telegramConnected ? "hover:border-blue-500/40" : "hover:border-blue-500/20"
        }`}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-base">
                <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-500/10">
                  <Send className="h-4 w-4 text-blue-400" />
                </span>
                Telegram
              </span>
              {telegramConnected ? (
                <Badge className="text-xs bg-blue-500/15 text-blue-400 border-blue-500/30 border">
                  <CheckCircle2 className="h-3 w-3 mr-1" /> Conectado
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">Não conectado</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Registre refeições, consulte resumos e configure lembretes direto no Telegram.
            </p>

            <ol className="space-y-2.5">
              <StepItem number={1}>
                Abra o Telegram e procure por{" "}
                <strong className="text-foreground font-mono">@CalorIA_bot</strong>
              </StepItem>
              <StepItem number={2}>
                Envie o comando{" "}
                <code className="bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded text-xs font-mono">/start</code>
              </StepItem>
              <StepItem number={3}>
                Gere um token abaixo e envie{" "}
                <code className="bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded text-xs font-mono">/conectar TOKEN</code>
              </StepItem>
            </ol>

            {telegramToken && (
              <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-sm font-mono break-all text-blue-300">
                    {telegramToken}
                  </code>
                  <button
                    className="cursor-pointer p-1.5 rounded-md hover:bg-blue-500/15 transition-colors text-muted-foreground hover:text-blue-400 shrink-0"
                    onClick={() => copyToClipboard(telegramToken, "telegram")}
                    title="Copiar"
                  >
                    {copied === "telegram"
                      ? <Check className="h-3.5 w-3.5 text-green-500" />
                      : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-2">
                  <Clock className="h-3 w-3" /> Válido por 10 minutos
                </p>
              </div>
            )}

            <Button
              onClick={async () => {
                const res = await generateTelegram.mutateAsync();
                setTelegramToken(res.token);
              }}
              disabled={generateTelegram.isPending}
              variant={telegramToken ? "outline" : "default"}
              className="gap-1.5 w-full"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${generateTelegram.isPending ? "animate-spin" : ""}`} />
              {generateTelegram.isPending
                ? "Gerando..."
                : telegramToken
                ? "Gerar novo token"
                : "Gerar token"}
            </Button>
          </CardContent>
        </Card>

        {/* WhatsApp */}
        <Card className={`transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl ${
          whatsappConnected ? "hover:border-green-500/40" : "hover:border-green-500/20"
        }`}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-base">
                <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-green-500/10">
                  <MessageSquare className="h-4 w-4 text-green-400" />
                </span>
                WhatsApp
              </span>
              {whatsappConnected ? (
                <Badge className="text-xs bg-green-500/15 text-green-400 border-green-500/30 border">
                  <CheckCircle2 className="h-3 w-3 mr-1" /> Conectado
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">Não conectado</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Use os mesmos recursos do Telegram via WhatsApp com comandos prefixados por{" "}
              <code className="bg-green-500/10 text-green-400 px-1 rounded text-xs font-mono">!</code>.
            </p>

            <ol className="space-y-2.5">
              <StepItem number={1}>
                Salve o número do bot nos seus contatos
              </StepItem>
              <StepItem number={2}>
                Envie o comando{" "}
                <code className="bg-green-500/10 text-green-400 px-1.5 py-0.5 rounded text-xs font-mono">!start</code>
              </StepItem>
              <StepItem number={3}>
                Gere um token abaixo e envie{" "}
                <code className="bg-green-500/10 text-green-400 px-1.5 py-0.5 rounded text-xs font-mono">!conectar TOKEN</code>
              </StepItem>
            </ol>

            {whatsappToken && (
              <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3">
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-sm font-mono break-all text-green-300">
                    {whatsappToken}
                  </code>
                  <button
                    className="cursor-pointer p-1.5 rounded-md hover:bg-green-500/15 transition-colors text-muted-foreground hover:text-green-400 shrink-0"
                    onClick={() => copyToClipboard(whatsappToken, "whatsapp")}
                    title="Copiar"
                  >
                    {copied === "whatsapp"
                      ? <Check className="h-3.5 w-3.5 text-green-500" />
                      : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-2">
                  <Clock className="h-3 w-3" /> Válido por 10 minutos
                </p>
              </div>
            )}

            <Button
              onClick={async () => {
                const res = await generateWhatsApp.mutateAsync();
                setWhatsappToken(res.token);
              }}
              disabled={generateWhatsApp.isPending}
              variant={whatsappToken ? "outline" : "default"}
              className="gap-1.5 w-full"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${generateWhatsApp.isPending ? "animate-spin" : ""}`} />
              {generateWhatsApp.isPending
                ? "Gerando..."
                : whatsappToken
                ? "Gerar novo token"
                : "Gerar token"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
