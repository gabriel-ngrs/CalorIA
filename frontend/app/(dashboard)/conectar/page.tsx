"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, Clock, Copy, MessageCircle, RefreshCw } from "lucide-react";
import { useGenerateTelegramToken, useGenerateWhatsAppToken, useMe } from "@/lib/hooks/useProfile";

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

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
            <MessageCircle className="h-6 w-6 text-primary" />
            Conectar Bot
          </h1>
        <p className="text-muted-foreground text-sm">Vincule seus canais de mensagem</p>
      </div>

      {/* Telegram */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Telegram
            {user?.telegram_chat_id ? (
              <Badge variant="default" className="text-xs">Conectado</Badge>
            ) : (
              <Badge variant="secondary" className="text-xs">Não conectado</Badge>
            )}
          </CardTitle>
          <CardDescription>
            Registre refeições, consulte resumos e configure lembretes direto no Telegram.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
            <li>Abra o Telegram e procure por <strong>@CalorIA_bot</strong></li>
            <li>Envie <code className="bg-muted px-1 rounded">/start</code></li>
            <li>Gere um token abaixo e envie <code className="bg-muted px-1 rounded">/conectar TOKEN</code></li>
          </ol>

          {telegramToken && (
            <div className="flex items-center gap-2 p-2 bg-muted rounded-md">
              <code className="flex-1 text-sm break-all">{telegramToken}</code>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => copyToClipboard(telegramToken, "telegram")}
              >
                {copied === "telegram" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
            </div>
          )}

          <Button
            onClick={async () => {
              const res = await generateTelegram.mutateAsync();
              setTelegramToken(res.token);
            }}
            disabled={generateTelegram.isPending}
            variant={telegramToken ? "outline" : "default"}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            {telegramToken ? "Gerar novo token" : "Gerar token"}
          </Button>
          {telegramToken && (
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" /> Válido por 10 minutos</p>
          )}
        </CardContent>
      </Card>

      {/* WhatsApp */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            WhatsApp
            {user?.whatsapp_number ? (
              <Badge variant="default" className="text-xs">Conectado</Badge>
            ) : (
              <Badge variant="secondary" className="text-xs">Não conectado</Badge>
            )}
          </CardTitle>
          <CardDescription>
            Use os mesmos recursos do Telegram via WhatsApp com comandos prefixados por <code>!</code>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
            <li>Salve o número do bot no seus contatos</li>
            <li>Envie <code className="bg-muted px-1 rounded">!start</code></li>
            <li>Gere um token abaixo e envie <code className="bg-muted px-1 rounded">!conectar TOKEN</code></li>
          </ol>

          {whatsappToken && (
            <div className="flex items-center gap-2 p-2 bg-muted rounded-md">
              <code className="flex-1 text-sm break-all">{whatsappToken}</code>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => copyToClipboard(whatsappToken, "whatsapp")}
              >
                {copied === "whatsapp" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
            </div>
          )}

          <Button
            onClick={async () => {
              const res = await generateWhatsApp.mutateAsync();
              setWhatsappToken(res.token);
            }}
            disabled={generateWhatsApp.isPending}
            variant={whatsappToken ? "outline" : "default"}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            {whatsappToken ? "Gerar novo token" : "Gerar token"}
          </Button>
          {whatsappToken && (
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" /> Válido por 10 minutos</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
