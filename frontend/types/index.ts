// ─── Auth ──────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ─── User / Profile ────────────────────────────────────────────────────────

export type Sex = "male" | "female";
export type ActivityLevel =
  | "sedentary"
  | "lightly_active"
  | "moderately_active"
  | "very_active"
  | "extra_active";
export type GoalType = "lose_weight" | "gain_muscle" | "maintain" | "body_recomp";

export interface UserProfile {
  height_cm: number | null;
  current_weight_kg: number | null;
  age: number | null;
  sex: Sex | null;
  activity_level: ActivityLevel | null;
  tdee_calculated: number | null;
}

export interface User {
  id: number;
  name: string;
  email: string;
  calorie_goal: number | null;
  weight_goal: number | null;
  water_goal_ml: number | null;
  goal_type: GoalType | null;
  profile: UserProfile | null;
  created_at: string;
}

// ─── Meals ─────────────────────────────────────────────────────────────────

export type MealType =
  | "breakfast"
  | "morning_snack"
  | "lunch"
  | "afternoon_snack"
  | "dinner"
  | "supper"
  | "snack"
  | "pre_workout"
  | "post_workout"
  | "supplement"
  | "dessert";
export type MealSource = "manual" | "telegram" | "whatsapp";

export interface MealItem {
  id: number;
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber: number | null;
  food_id: number | null;
  data_source: string | null; // "taco" | "openfoodfacts" | "usda" | "ai_estimated" | null
  sodium: number | null;
  sugar: number | null;
  saturated_fat: number | null;
}

export interface Meal {
  id: number;
  meal_type: MealType;
  date: string;
  source: MealSource;
  notes: string | null;
  items: MealItem[];
}

export interface MealItemCreate {
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber?: number;
  food_id?: number | null;
  data_source?: string | null;
  sodium?: number | null;
  sugar?: number | null;
  saturated_fat?: number | null;
}

export interface MealCreate {
  meal_type: MealType;
  date: string;
  source?: MealSource;
  notes?: string;
  items: MealItemCreate[];
}

export interface MealUpdate {
  meal_type?: MealType;
  date?: string;
  notes?: string;
  name?: string;
}

// ─── Logs ──────────────────────────────────────────────────────────────────

export interface WeightLog {
  id: number;
  weight_kg: number;
  date: string;
  notes: string | null;
}

export interface HydrationLog {
  id: number;
  amount_ml: number;
  date: string;
  time: string;
}

export interface HydrationDaySummary {
  date: string;
  total_ml: number;
  entries_count: number;
}

export interface MoodLog {
  id: number;
  date: string;
  energy_level: number;
  mood_level: number;
  notes: string | null;
}

// ─── Reminders ─────────────────────────────────────────────────────────────

export type ReminderType = "meal" | "water" | "weight" | "daily_summary" | "custom";

export interface Reminder {
  id: number;
  type: ReminderType;
  time: string;
  days_of_week: number[];
  active: boolean;
  message: string | null;
}

// ─── Push Notifications ─────────────────────────────────────────────────────

export interface PushSubscriptionPayload {
  endpoint: string;
  p256dh: string;
  auth: string;
  user_agent?: string;
}

export type NotificationType =
  | "reminder"
  | "daily_summary"
  | "weekly_report"
  | "hydration"
  | "system";

export interface AppNotification {
  id: number;
  type: NotificationType;
  title: string;
  body: string;
  read: boolean;
  created_at: string;
}

// ─── Dashboard ─────────────────────────────────────────────────────────────

export interface MealSummaryItem {
  id: number;
  food_name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
}

export interface MealSummary {
  meal_type: MealType;
  items: MealSummaryItem[];
}

export interface NutritionSummary {
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  meals_count: number;
  meals: MealSummary[];
}

export interface HydrationSummary {
  total_ml: number;
}

export interface DashboardToday {
  date: string;
  nutrition: NutritionSummary;
  hydration: HydrationSummary;
  mood: MoodLog | null;
  latest_weight: WeightLog | null;
}

export interface WeeklySummary {
  start_date: string;
  end_date: string;
  total_days_logged: number;
  avg_calories: number;
  avg_protein: number;
  avg_carbs: number;
  avg_fat: number;
}

export interface WeightChartPoint {
  date: string;
  weight_kg: number;
}

export interface WeeklyMacroPoint {
  date: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
}

// ─── AI ────────────────────────────────────────────────────────────────────

export interface ParsedFoodItem {
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber: number;
  confidence: number;
  food_id: number | null;
  data_source: string | null; // "taco" | "openfoodfacts" | "usda" | "ai_estimated" | null
  sodium: number | null;
  sugar: number | null;
  saturated_fat: number | null;
}

export interface MealAnalysisResponse {
  items: ParsedFoodItem[];
  low_confidence: boolean;
}

export interface InsightResponse {
  type: string;
  content: string;
  generated_at: string;
}

export interface SuggestedMealItem {
  food_name: string;
  quantity: number;
  unit: string;
  estimated_calories: number;
}

export interface MealSuggestion {
  name: string;
  description: string;
  meal_type: string;
  estimated_calories: number;
  items: SuggestedMealItem[];
}

export interface EatingPattern {
  analysis: string;
  frequent_foods: string[];
  days_analyzed: number;
}

export interface NutritionalAlert {
  nutrient: string;
  average_daily: number;
  recommended_min: number;
  unit: string;
  severity: "low" | "medium" | "high";
}

export interface NutritionalAlertsResponse {
  alerts: NutritionalAlert[];
  analysis: string;
  days_analyzed: number;
}

export interface GoalAdjustmentSuggestion {
  current_calorie_goal: number | null;
  suggested_calorie_goal: number | null;
  current_weight_goal: number | null;
  weight_trend_kg_per_week: number | null;
  adjustment_recommended: boolean;
  suggestion: string;
}

export interface WeekSummary {
  week_number: number;
  start_date: string;
  end_date: string;
  avg_calories: number;
  days_logged: number;
  adherence_pct: number;
}

export interface MonthlyReport {
  month: number;
  year: number;
  total_days_logged: number;
  adherence_score: number;
  avg_daily_calories: number;
  avg_daily_protein: number;
  avg_daily_carbs: number;
  avg_daily_fat: number;
  best_week: WeekSummary;
  worst_week: WeekSummary;
  analysis: string;
}

// ─── next-auth session augmentation ────────────────────────────────────────

declare module "next-auth" {
  interface User {
    accessToken: string;
    refreshToken: string;
  }

  interface Session {
    accessToken: string;
    refreshToken: string;
    error?: string;
    accessTokenExpires?: number;
    user: {
      id: string;
      name: string;
      email: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken: string;
    refreshToken: string;
    accessTokenExpires: number;
    error?: string;
    id: string;
  }
}
