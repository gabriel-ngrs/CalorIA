"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Flame,
  MessageSquare,
  RefreshCw,
  Send,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  useMe,
  useProfile,
  useUpdateMe,
  useUpdateProfile,
  useGenerateTelegramToken,
  useGenerateWhatsAppToken,
} from "@/lib/hooks/useProfile";
import type { ActivityLevel, GoalType, Sex } from "@/types";

// ─── Label maps ──────────────────────────────────────────────────────────────

const SEX_LABELS: Record<Sex, string> = {
  male: "Masculino",
  female: "Feminino",
};

const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: "Sedentário",
  lightly_active: "Levemente ativo",
  moderately_active: "Moderadamente ativo",
  very_active: "Muito ativo",
  extra_active: "Extremamente ativo",
};

const GOAL_LABELS: Record<GoalType, string> = {
  lose_weight: "Perder peso",
  gain_muscle: "Ganhar músculo",
  maintain: "Manter peso",
  body_recomp: "Recomposição corporal",
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function StepDots({ step }: { step: number }) {
  return (
    <div className="flex gap-2 mb-6">
      {[1, 2, 3].map((n) => (
        <span
          key={n}
          className={cn(
            "h-2 rounded-full transition-all duration-300",
            n === step
              ? "w-8 bg-primary"
              : n < step
              ? "w-4 bg-primary/60"
              : "w-4 bg-muted"
          )}
        />
      ))}
    </div>
  );
}

function FieldLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <Label
      htmlFor={htmlFor}
      className="text-xs font-medium text-muted-foreground uppercase tracking-wide"
    >
      {children}
    </Label>
  );
}

// ─── Step 1 — Dados físicos ───────────────────────────────────────────────────

interface Step1Fields {
  weight: string;
  height: string;
  age: string;
  sex: Sex | "";
  activity: ActivityLevel | "";
}

function Step1({
  fields,
  onChange,
}: {
  fields: Step1Fields;
  onChange: (f: Partial<Step1Fields>) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <FieldLabel htmlFor="weight">Peso atual (kg)</FieldLabel>
          <Input
            id="weight"
            placeholder="70"
            inputMode="decimal"
            value={fields.weight}
            onChange={(e) => onChange({ weight: e.target.value })}
          />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="height">Altura (cm)</FieldLabel>
          <Input
            id="height"
            placeholder="170"
            inputMode="numeric"
            value={fields.height}
            onChange={(e) => onChange({ height: e.target.value })}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <FieldLabel htmlFor="age">Idade (anos)</FieldLabel>
        <Input
          id="age"
          placeholder="25"
          inputMode="numeric"
          value={fields.age}
          onChange={(e) => onChange({ age: e.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <FieldLabel htmlFor="sex">Sexo</FieldLabel>
        <Select
          value={fields.sex}
          onValueChange={(v) => onChange({ sex: v as Sex })}
        >
          <SelectTrigger id="sex">
            <SelectValue placeholder="Selecione..." />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(SEX_LABELS) as Sex[]).map((key) => (
              <SelectItem key={key} value={key}>
                {SEX_LABELS[key]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <FieldLabel htmlFor="activity">Nível de atividade</FieldLabel>
        <Select
          value={fields.activity}
          onValueChange={(v) => onChange({ activity: v as ActivityLevel })}
        >
          <SelectTrigger id="activity">
            <SelectValue placeholder="Selecione..." />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(ACTIVITY_LABELS) as ActivityLevel[]).map((key) => (
              <SelectItem key={key} value={key}>
                {ACTIVITY_LABELS[key]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

// ─── Step 2 — Metas ───────────────────────────────────────────────────────────

interface Step2Fields {
  calorieGoal: string;
  waterGoal: string;
  weightGoal: string;
  goalType: GoalType | "";
}

function Step2({
  fields,
  onChange,
  tdee,
}: {
  fields: Step2Fields;
  onChange: (f: Partial<Step2Fields>) => void;
  tdee: number | null | undefined;
}) {
  return (
    <div className="space-y-4">
      {tdee != null && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/8 border border-primary/20 text-sm text-primary">
          <Flame className="h-4 w-4 shrink-0" />
          <span>
            Gasto estimado:{" "}
            <strong>{Math.round(tdee).toLocaleString("pt-BR")} kcal/dia</strong>
          </span>
        </div>
      )}

      <div className="space-y-1.5">
        <FieldLabel htmlFor="calorieGoal">Meta calórica (kcal/dia)</FieldLabel>
        <Input
          id="calorieGoal"
          placeholder={tdee ? String(Math.round(tdee)) : "2000"}
          inputMode="numeric"
          value={fields.calorieGoal}
          onChange={(e) => onChange({ calorieGoal: e.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <FieldLabel htmlFor="waterGoal">Meta hídrica (ml/dia)</FieldLabel>
        <Input
          id="waterGoal"
          placeholder="2000"
          inputMode="numeric"
          value={fields.waterGoal}
          onChange={(e) => onChange({ waterGoal: e.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <FieldLabel htmlFor="weightGoal">Meta de peso (kg)</FieldLabel>
        <Input
          id="weightGoal"
          placeholder="65"
          inputMode="decimal"
          value={fields.weightGoal}
          onChange={(e) => onChange({ weightGoal: e.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <FieldLabel htmlFor="goalType">Objetivo</FieldLabel>
        <Select
          value={fields.goalType}
          onValueChange={(v) => onChange({ goalType: v as GoalType })}
        >
          <SelectTrigger id="goalType">
            <SelectValue placeholder="Selecione..." />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(GOAL_LABELS) as GoalType[]).map((key) => (
              <SelectItem key={key} value={key}>
                {GOAL_LABELS[key]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

// ─── Step 3 — Conectar bots ───────────────────────────────────────────────────

function BotCard({
  channel,
  connected,
  token,
  isPending,
  copied,
  onGenerate,
  onCopy,
}: {
  channel: "telegram" | "whatsapp";
  connected: boolean;
  token: string | null;
  isPending: boolean;
  copied: boolean;
  onGenerate: () => void;
  onCopy: () => void;
}) {
  const isTelegram = channel === "telegram";
  const color = isTelegram ? "blue" : "green";

  const colorMap = {
    blue: {
      icon: "bg-blue-500/10",
      iconText: "text-blue-400",
      badge: "bg-blue-500/15 text-blue-400 border-blue-500/30 border",
      token: "border-blue-500/20 bg-blue-500/5",
      tokenText: "text-blue-300",
      copyHover: "hover:bg-blue-500/15 hover:text-blue-400",
      code: "bg-blue-500/10 text-blue-400",
      cardHover: connected ? "hover:border-blue-500/40" : "hover:border-blue-500/20",
    },
    green: {
      icon: "bg-green-500/10",
      iconText: "text-green-400",
      badge: "bg-green-500/15 text-green-400 border-green-500/30 border",
      token: "border-green-500/20 bg-green-500/5",
      tokenText: "text-green-300",
      copyHover: "hover:bg-green-500/15 hover:text-green-400",
      code: "bg-green-500/10 text-green-400",
      cardHover: connected ? "hover:border-green-500/40" : "hover:border-green-500/20",
    },
  };

  const c = colorMap[color];
  const prefix = isTelegram ? "/" : "!";

  return (
    <Card
      className={cn(
        "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl",
        c.cardHover
      )}
    >
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-base">
            <span
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-lg",
                c.icon
              )}
            >
              {isTelegram ? (
                <Send className={cn("h-4 w-4", c.iconText)} />
              ) : (
                <MessageSquare className={cn("h-4 w-4", c.iconText)} />
              )}
            </span>
            {isTelegram ? "Telegram" : "WhatsApp"}
          </span>
          {connected ? (
            <Badge className={cn("text-xs", c.badge)}>
              <CheckCircle2 className="h-3 w-3 mr-1" /> Conectado
            </Badge>
          ) : (
            <Badge variant="secondary" className="text-xs">
              Não conectado
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-2">
          <li className="flex items-start gap-3">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/15 text-primary text-[11px] font-bold shrink-0 mt-0.5">
              1
            </span>
            <span className="text-sm text-muted-foreground leading-relaxed">
              {isTelegram ? (
                <>
                  Procure por{" "}
                  <strong className="text-foreground font-mono">
                    @CalorIA_bot
                  </strong>{" "}
                  no Telegram
                </>
              ) : (
                "Salve o número do bot nos seus contatos"
              )}
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/15 text-primary text-[11px] font-bold shrink-0 mt-0.5">
              2
            </span>
            <span className="text-sm text-muted-foreground leading-relaxed">
              Envie{" "}
              <code
                className={cn(
                  "px-1.5 py-0.5 rounded text-xs font-mono",
                  c.code
                )}
              >
                {prefix}start
              </code>
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/15 text-primary text-[11px] font-bold shrink-0 mt-0.5">
              3
            </span>
            <span className="text-sm text-muted-foreground leading-relaxed">
              Gere um token e envie{" "}
              <code
                className={cn(
                  "px-1.5 py-0.5 rounded text-xs font-mono",
                  c.code
                )}
              >
                {prefix}conectar TOKEN
              </code>
            </span>
          </li>
        </ol>

        {token && (
          <div
            className={cn(
              "rounded-lg border p-3",
              c.token
            )}
          >
            <div className="flex items-center gap-2">
              <code
                className={cn(
                  "flex-1 text-sm font-mono break-all",
                  c.tokenText
                )}
              >
                {token}
              </code>
              <button
                className={cn(
                  "cursor-pointer p-1.5 rounded-md transition-colors text-muted-foreground shrink-0",
                  c.copyHover
                )}
                onClick={onCopy}
                title="Copiar"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-green-500" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1 mt-2">
              <Clock className="h-3 w-3" /> Válido por 10 minutos
            </p>
          </div>
        )}

        <Button
          onClick={onGenerate}
          disabled={isPending}
          variant={token ? "outline" : "default"}
          className="gap-1.5 w-full"
        >
          <RefreshCw
            className={cn("h-3.5 w-3.5", isPending && "animate-spin")}
          />
          {isPending
            ? "Gerando..."
            : token
            ? "Gerar novo token"
            : "Gerar token"}
        </Button>
      </CardContent>
    </Card>
  );
}

function Step3() {
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
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Conecte o bot do Telegram ou WhatsApp para registrar refeições por
        mensagem. Você pode pular e conectar depois.
      </p>

      <BotCard
        channel="telegram"
        connected={!!user?.telegram_chat_id}
        token={telegramToken}
        isPending={generateTelegram.isPending}
        copied={copied === "telegram"}
        onGenerate={async () => {
          try {
            const res = await generateTelegram.mutateAsync();
            setTelegramToken(res.token);
          } catch {
            toast.error("Erro ao gerar token do Telegram.");
          }
        }}
        onCopy={() => telegramToken && copyToClipboard(telegramToken, "telegram")}
      />

      <BotCard
        channel="whatsapp"
        connected={!!user?.whatsapp_number}
        token={whatsappToken}
        isPending={generateWhatsApp.isPending}
        copied={copied === "whatsapp"}
        onGenerate={async () => {
          try {
            const res = await generateWhatsApp.mutateAsync();
            setWhatsappToken(res.token);
          } catch {
            toast.error("Erro ao gerar token do WhatsApp.");
          }
        }}
        onCopy={() => whatsappToken && copyToClipboard(whatsappToken, "whatsapp")}
      />
    </div>
  );
}

// ─── Onboarding page ─────────────────────────────────────────────────────────

const STEP_TITLES = [
  "Seus dados físicos",
  "Suas metas",
  "Conectar bots",
];
const STEP_DESCRIPTIONS = [
  "Vamos calcular suas necessidades nutricionais",
  "Defina seus objetivos de saúde",
  "Registre refeições pelo Telegram ou WhatsApp (opcional)",
];

function parseNum(value: string): number | null {
  if (!value.trim()) return null;
  const n = parseFloat(value.replace(",", "."));
  return isNaN(n) ? null : n;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { data: user } = useMe();
  const { data: profile } = useProfile();
  const updateProfile = useUpdateProfile();
  const updateMe = useUpdateMe();

  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);

  // Step 1 state
  const [step1, setStep1] = useState<Step1Fields>({
    weight: "",
    height: "",
    age: "",
    sex: "",
    activity: "",
  });

  // Step 2 state
  const [step2, setStep2] = useState<Step2Fields>({
    calorieGoal: "",
    waterGoal: "2000",
    weightGoal: "",
    goalType: "",
  });

  // Pre-populate from existing data
  useEffect(() => {
    if (profile) {
      setStep1((prev) => ({
        ...prev,
        weight: profile.current_weight_kg != null ? String(profile.current_weight_kg) : prev.weight,
        height: profile.height_cm != null ? String(profile.height_cm) : prev.height,
        age: profile.age != null ? String(profile.age) : prev.age,
        sex: profile.sex ?? prev.sex,
        activity: profile.activity_level ?? prev.activity,
      }));
    }
  }, [profile]);

  useEffect(() => {
    if (user) {
      setStep2((prev) => ({
        ...prev,
        calorieGoal: user.calorie_goal != null ? String(user.calorie_goal) : prev.calorieGoal,
        waterGoal: user.water_goal_ml != null ? String(user.water_goal_ml) : prev.waterGoal,
        weightGoal: user.weight_goal != null ? String(user.weight_goal) : prev.weightGoal,
        goalType: user.goal_type ?? prev.goalType,
      }));
    }
  }, [user]);

  async function handleNext() {
    setSaving(true);
    try {
      if (step === 1) {
        await updateProfile.mutateAsync({
          current_weight_kg: parseNum(step1.weight) ?? undefined,
          height_cm: parseNum(step1.height) ?? undefined,
          age: parseNum(step1.age) ?? undefined,
          sex: step1.sex || undefined,
          activity_level: step1.activity || undefined,
        } as Parameters<typeof updateProfile.mutateAsync>[0]);
        toast.success("Dados físicos salvos!");
        setStep(2);
      } else if (step === 2) {
        await updateMe.mutateAsync({
          calorie_goal: parseNum(step2.calorieGoal) ?? undefined,
          water_goal_ml: parseNum(step2.waterGoal) ?? undefined,
          weight_goal: parseNum(step2.weightGoal) ?? undefined,
          goal_type: step2.goalType || undefined,
        } as Parameters<typeof updateMe.mutateAsync>[0]);
        toast.success("Metas salvas!");
        setStep(3);
      }
    } catch {
      toast.error("Erro ao salvar. Verifique os dados e tente novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSkip() {
    if (step === 2) {
      // Salva meta calórica padrão para evitar loop no redirect do dashboard
      try {
        await updateMe.mutateAsync({ calorie_goal: 2000 } as Parameters<typeof updateMe.mutateAsync>[0]);
      } catch { /* silencia — usuário pode configurar depois */ }
      setStep(3);
    } else if (step < 3) {
      setStep((s) => s + 1);
    } else {
      router.replace("/dashboard");
    }
  }

  function handleFinish() {
    router.replace("/dashboard");
  }

  const isLastStep = step === 3;

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-10"
      style={{
        background: [
          "radial-gradient(ellipse 70% 50% at 10% 0%, hsl(198 38% 20% / 0.22) 0%, transparent 55%)",
          "radial-gradient(ellipse 55% 40% at 90% 100%, hsl(215 40% 18% / 0.20) 0%, transparent 52%)",
          "radial-gradient(ellipse 40% 30% at 50% 50%, hsl(28 88% 54% / 0.06) 0%, transparent 60%)",
          "hsl(var(--background))",
        ].join(", "),
      }}
    >
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-1">CalorIA</h1>
          <p className="text-sm text-muted-foreground">
            Vamos configurar seu perfil em poucos passos
          </p>
        </div>

        {/* Step dots */}
        <div className="flex justify-center">
          <StepDots step={step} />
        </div>

        {/* Card */}
        <Card className="border-border/60 bg-card/90 shadow-xl backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">{STEP_TITLES[step - 1]}</CardTitle>
            <CardDescription>{STEP_DESCRIPTIONS[step - 1]}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-2 pt-2">
            {step === 1 && (
              <Step1
                fields={step1}
                onChange={(f) => setStep1((prev) => ({ ...prev, ...f }))}
              />
            )}
            {step === 2 && (
              <Step2
                fields={step2}
                onChange={(f) => setStep2((prev) => ({ ...prev, ...f }))}
                tdee={profile?.tdee_calculated}
              />
            )}
            {step === 3 && <Step3 />}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="mt-4 space-y-3">
          <div className="flex gap-3">
            {step > 1 && (
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setStep((s) => s - 1)}
                disabled={saving}
              >
                Voltar
              </Button>
            )}

            {isLastStep ? (
              <Button className="flex-1" onClick={handleFinish}>
                Concluir
              </Button>
            ) : (
              <Button
                className="flex-1"
                onClick={handleNext}
                disabled={saving}
              >
                {saving ? "Salvando..." : "Próximo"}
              </Button>
            )}
          </div>

          <div className="text-center">
            <button
              onClick={handleSkip}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline cursor-pointer"
            >
              Pular esta etapa
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
