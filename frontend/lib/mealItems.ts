import type { MealItemCreate, ParsedFoodItem } from "@/types";

/**
 * Converte um item analisado pela IA no payload de criação de refeição.
 *
 * Existe para que a **procedência do valor nutricional** não se perca no
 * caminho. Duas telas montavam esse payload à mão copiando só os macros, e
 * ambas descartavam `food_id`, `data_source`, os micronutrientes e a porção
 * descrita pelo usuário — a tela de revisão dizia "veio da tabela nutricional"
 * e a refeição gravada não sabia mais responder isso.
 *
 * Um único ponto de conversão garante que adicionar um campo de rastreabilidade
 * ao pipeline não exija lembrar de propagá-lo em cada tela.
 */
export function toMealItemCreate(item: ParsedFoodItem): MealItemCreate {
  return {
    food_name: item.food_name,
    // `quantity` já é a massa normalizada em gramas pela tabela de porções.
    quantity: item.quantity,
    unit: item.unit,
    calories: item.calories,
    protein: item.protein,
    carbs: item.carbs,
    fat: item.fat,
    fiber: item.fiber,
    // Rastreabilidade da origem do número.
    food_id: item.food_id,
    data_source: item.data_source,
    sodium: item.sodium,
    sugar: item.sugar,
    saturated_fat: item.saturated_fat,
    // A porção como a pessoa descreveu ("8 fatia"), para que a refeição
    // gravada consiga explicar de onde saíram os gramas.
    raw_input: item.portion_text ?? undefined,
  };
}
