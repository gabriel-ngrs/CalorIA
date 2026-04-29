"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Check,
  Droplets,
  Flame,
  Scale,
  Target,
  User,
  Ruler,
  Calendar,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useMe, useProfile, useUpdateProfile, useUpdateMe } from "@/lib/hooks/useProfile";
import { toast } from "sonner";
import type { ActivityLevel, GoalType, Sex } from "@/types";

const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: "Sedentário (sem exercício)",
  lightly_active: "Levemente ativo (1-3x/semana)",
  moderately_active: "Moderadamente ativo (3-5x/semana)",
  very_active: "Muito ativo (6-7x/semana)",
  extra_active: "Extremamente ativo (atleta)",
};

const GOAL_TYPE_LABELS: Record<GoalType, string> = {
  lose_weight: "Emagrecer",
  gain_muscle: "Ganhar massa muscular",
  maintain: "Manter peso",
  body_recomp: "Recomposição corporal",
};

const GOAL_TYPE_COLORS: Record<GoalType, string> = {
  lose_weight:  "text-blue-400",
  gain_muscle:  "text-orange-400",
  maintain:     "text-green-400",
  body_recomp:  "text-purple-400",
};

export default function PerfilPage() {
  const { data: user } = useMe();
  const { data: profile } = useProfile();
  const updateProfile = useUpdateProfile();
  const updateMe = useUpdateMe();

  const [name, setName] = useState("");
  const [calorieGoal, setCalorieGoal] = useState("");
  const [weightGoal, setWeightGoal] = useState("");
  const [waterGoal, setWaterGoal] = useState("");
  const [goalType, setGoalType] = useState<GoalType | "">("");
  const [height, setHeight] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState<Sex | "">("");
  const [activity, setActivity] = useState<ActivityLevel | "">("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setName(user.name ?? "");
      setCalorieGoal(user.calorie_goal?.toString() ?? "");
      setWeightGoal(user.weight_goal?.toString() ?? "");
      setWaterGoal(user.water_goal_ml?.toString() ?? "");
      setGoalType(user.goal_type ?? "");
    }
  }, [user]);

  useEffect(() => {
    if (profile) {
      setHeight(profile.height_cm?.toString() ?? "");
      setAge(profile.age?.toString() ?? "");
      setSex(profile.sex ?? "");
      setActivity(profile.activity_level ?? "");
    }
  }, [profile]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const profilePayload: Record<string, unknown> = {};
    if (height) profilePayload.height_cm = Number(height);
    if (age) profilePayload.age = Number(age);
    if (sex) profilePayload.sex = sex;
    if (activity) profilePayload.activity_level = activity;

    const mePayload: Record<string, unknown> = { name };
    if (calorieGoal) mePayload.calorie_goal = Number(calorieGoal);
    if (weightGoal) mePayload.weight_goal = Number(weightGoal);
    if (waterGoal) mePayload.water_goal_ml = Number(waterGoal);
    if (goalType) mePayload.goal_type = goalType;

    await Promise.all([
      updateProfile.mutateAsync(profilePayload),
      updateMe.mutateAsync(mePayload),
    ]);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    toast.success("Perfil atualizado!");
  }

  const isPending = updateProfile.isPending || updateMe.isPending;

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-gray-900 flex items-center gap-2">
          <User className="h-6 w-6 text-primary" />
          Perfil
        </h1>
        <p className="text-gray-400 text-sm">Seus dados e metas</p>
      </div>

      {/* TDEE banner — destaque quando disponível */}
      {profile?.tdee_calculated && (
        <Card className="border-orange-500/30 bg-orange-500/5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-orange-500/50">
          <CardContent className="pt-5 pb-5">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-sm font-medium flex items-center gap-1.5 mb-1">
                  <span className="flex items-center justify-center w-6 h-6 rounded-md bg-orange-500/15">
                    <Flame className="h-3.5 w-3.5 text-orange-500" />
                  </span>
                  TDEE estimado
                </p>
                <p className="text-4xl font-bold text-orange-500">
                  {profile.tdee_calculated.toFixed(0)}
                  <span className="text-base font-normal text-muted-foreground ml-2">kcal/dia</span>
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Total Daily Energy Expenditure — Harris-Benedict
                </p>
              </div>
              {user?.calorie_goal && (
                <div className="text-right">
                  <p className="text-xs text-muted-foreground mb-0.5">Sua meta calórica</p>
                  <p className="text-2xl font-bold text-primary">
                    {user.calorie_goal}
                    <span className="text-sm font-normal text-muted-foreground ml-1">kcal</span>
                  </p>
                  <p className={`text-xs mt-0.5 font-medium ${
                    user.calorie_goal < profile.tdee_calculated ? "text-blue-400" :
                    user.calorie_goal > profile.tdee_calculated ? "text-orange-400" : "text-green-400"
                  }`}>
                    {user.calorie_goal < profile.tdee_calculated
                      ? `${(profile.tdee_calculated - user.calorie_goal).toFixed(0)} kcal abaixo do TDEE`
                      : user.calorie_goal > profile.tdee_calculated
                      ? `${(user.calorie_goal - profile.tdee_calculated).toFixed(0)} kcal acima do TDEE`
                      : "igual ao TDEE"}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Layout 2 colunas */}
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Coluna esquerda — dados pessoais + físicos */}
          <div className="space-y-4">

            {/* Dados pessoais */}
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-primary/30">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-primary/10">
                    <User className="h-3 w-3 text-primary" />
                  </span>
                  Dados pessoais
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="name" className="text-xs text-muted-foreground uppercase tracking-wide">Nome</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Seu nome"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="height" className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                      <Ruler className="h-3 w-3" /> Altura (cm)
                    </Label>
                    <Input
                      id="height"
                      type="number"
                      placeholder="175"
                      value={height}
                      onChange={(e) => setHeight(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="age" className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> Idade
                    </Label>
                    <Input
                      id="age"
                      type="number"
                      placeholder="30"
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground uppercase tracking-wide">Sexo</Label>
                  <Select value={sex} onValueChange={(v) => setSex(v as Sex)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Masculino</SelectItem>
                      <SelectItem value="female">Feminino</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Nível de atividade */}
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-blue-500/30">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-blue-500/10">
                    <Activity className="h-3 w-3 text-blue-400" />
                  </span>
                  Nível de atividade
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={activity} onValueChange={(v) => setActivity(v as ActivityLevel)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione seu nível de atividade" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ACTIVITY_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground mt-2">
                  Usado para calcular seu TDEE com precisão.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Coluna direita — metas */}
          <div className="space-y-4">

            {/* Objetivo */}
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-purple-500/30">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-purple-500/10">
                    <Target className="h-3 w-3 text-purple-400" />
                  </span>
                  Objetivo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={goalType} onValueChange={(v) => setGoalType(v as GoalType)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione seu objetivo" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(GOAL_TYPE_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>
                        <span className={`font-medium ${GOAL_TYPE_COLORS[v as GoalType]}`}>
                          {label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Metas numéricas */}
            <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:border-green-500/30">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md bg-green-500/10">
                    <Flame className="h-3 w-3 text-green-500" />
                  </span>
                  Metas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="cg" className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                    <Flame className="h-3 w-3 text-orange-500" /> Meta calórica (kcal/dia)
                  </Label>
                  <Input
                    id="cg"
                    type="number"
                    placeholder="2000"
                    value={calorieGoal}
                    onChange={(e) => setCalorieGoal(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="wg" className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                      <Scale className="h-3 w-3 text-green-500" /> Meta de peso (kg)
                    </Label>
                    <Input
                      id="wg"
                      type="number"
                      step="0.1"
                      placeholder="65.0"
                      value={weightGoal}
                      onChange={(e) => setWeightGoal(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="water" className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                      <Droplets className="h-3 w-3 text-blue-400" /> Água (ml/dia)
                    </Label>
                    <Input
                      id="water"
                      type="number"
                      step="100"
                      placeholder="2000"
                      value={waterGoal}
                      onChange={(e) => setWaterGoal(e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Botão salvar */}
            <Button type="submit" className="w-full" disabled={isPending}>
              {saved
                ? <><Check className="h-4 w-4 mr-1.5" /> Salvo!</>
                : isPending
                ? "Salvando..."
                : "Salvar alterações"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
