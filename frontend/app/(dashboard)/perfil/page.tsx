"use client";

import { useEffect, useState } from "react";
import { Check, Flame, User } from "lucide-react";
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
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <User className="h-6 w-6 text-primary" />
          Perfil
        </h1>
        <p className="text-muted-foreground text-sm">Seus dados e metas</p>
      </div>

      {profile?.tdee_calculated && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="pt-4">
            <p className="text-sm font-medium flex items-center gap-1.5">
              <Flame className="h-4 w-4 text-orange-500" />
              TDEE estimado
            </p>
            <p className="text-3xl font-bold">{profile.tdee_calculated.toFixed(0)} <span className="text-base font-normal text-muted-foreground">kcal/dia</span></p>
            <p className="text-xs text-muted-foreground mt-1">Total Daily Energy Expenditure (Harris-Benedict)</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Dados pessoais</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Nome</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} className="mt-1" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="height">Altura (cm)</Label>
                <Input id="height" type="number" placeholder="175" value={height} onChange={(e) => setHeight(e.target.value)} className="mt-1" />
              </div>
              <div>
                <Label htmlFor="age">Idade</Label>
                <Input id="age" type="number" placeholder="30" value={age} onChange={(e) => setAge(e.target.value)} className="mt-1" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Sexo</Label>
                <Select value={sex} onValueChange={(v) => setSex(v as Sex)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Masculino</SelectItem>
                    <SelectItem value="female">Feminino</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Nível de atividade</Label>
                <Select value={activity} onValueChange={(v) => setActivity(v as ActivityLevel)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ACTIVITY_LABELS).map(([v, label]) => (
                      <SelectItem key={v} value={v}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label>Objetivo</Label>
              <Select value={goalType} onValueChange={(v) => setGoalType(v as GoalType)}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecione seu objetivo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(GOAL_TYPE_LABELS).map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="border-t pt-4 space-y-3">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Metas</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="cg">Meta calórica (kcal)</Label>
                  <Input id="cg" type="number" placeholder="2000" value={calorieGoal} onChange={(e) => setCalorieGoal(e.target.value)} className="mt-1" />
                </div>
                <div>
                  <Label htmlFor="wg">Meta de peso (kg)</Label>
                  <Input id="wg" type="number" step="0.1" placeholder="65.0" value={weightGoal} onChange={(e) => setWeightGoal(e.target.value)} className="mt-1" />
                </div>
              </div>
              <div>
                <Label htmlFor="water">Meta de água (ml/dia)</Label>
                <Input id="water" type="number" step="100" placeholder="2000" value={waterGoal} onChange={(e) => setWaterGoal(e.target.value)} className="mt-1" />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={updateProfile.isPending || updateMe.isPending}>
              {saved ? <><Check className="h-4 w-4 mr-1.5" /> Salvo!</> : updateProfile.isPending ? "Salvando..." : "Salvar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
