import { weightGoalStatus } from "@/lib/weightGoal";

describe("weightGoalStatus", () => {
  describe("gain_muscle (regressão B14)", () => {
    it("peso abaixo da meta NÃO é meta atingida — faltam kg para subir", () => {
      // Cenário do bug: objetivo ganhar massa, atual 81, meta 90.
      const s = weightGoalStatus({
        current: 81,
        goal: 90,
        start: 78,
        goalType: "gain_muscle",
      });
      expect(s.reached).toBe(false);
      expect(s.remainingKg).toBeCloseTo(9);
      expect(s.progressPct).toBeCloseTo(25); // (81-78)/(90-78) = 3/12
    });

    it("peso igual/acima da meta é atingida", () => {
      const s = weightGoalStatus({
        current: 90,
        goal: 90,
        start: 78,
        goalType: "gain_muscle",
      });
      expect(s.reached).toBe(true);
      expect(s.remainingKg).toBe(0);
      expect(s.progressPct).toBe(100);
    });
  });

  describe("lose_weight", () => {
    it("peso abaixo da meta é atingida", () => {
      const s = weightGoalStatus({
        current: 74,
        goal: 75,
        start: 82,
        goalType: "lose_weight",
      });
      expect(s.reached).toBe(true);
      expect(s.remainingKg).toBe(0);
    });

    it("peso acima da meta: faltam kg para descer", () => {
      const s = weightGoalStatus({
        current: 80,
        goal: 75,
        start: 85,
        goalType: "lose_weight",
      });
      expect(s.reached).toBe(false);
      expect(s.remainingKg).toBeCloseTo(5);
      expect(s.progressPct).toBeCloseTo(50); // (85-80)/(85-75)
    });

    it("sem goalType assume lose_weight (compatibilidade)", () => {
      const s = weightGoalStatus({ current: 74, goal: 75, start: 82 });
      expect(s.reached).toBe(true);
    });
  });

  describe("maintain / body_recomp", () => {
    it("dentro da tolerância é atingida", () => {
      const s = weightGoalStatus({
        current: 80.5,
        goal: 80,
        start: 85,
        goalType: "maintain",
      });
      expect(s.reached).toBe(true);
    });

    it("fora da tolerância: mostra distância como faltante", () => {
      const s = weightGoalStatus({
        current: 83,
        goal: 80,
        start: 85,
        goalType: "body_recomp",
      });
      expect(s.reached).toBe(false);
      expect(s.remainingKg).toBeCloseTo(3);
    });
  });
});
