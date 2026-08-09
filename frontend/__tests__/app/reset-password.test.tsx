import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ResetPasswordPage from "@/app/(auth)/reset-password/page";

const mockPost = jest.fn();
const mockPush = jest.fn();
let mockToken: string | null = "tok123";

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: { post: (...args: unknown[]) => mockPost(...args) },
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: () => mockToken }),
}));

describe("ResetPasswordPage — definir nova senha (FR-D4)", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockPush.mockReset();
    mockToken = "tok123";
  });

  it("envia token + nova senha e confirma o sucesso", async () => {
    mockPost.mockResolvedValue({});
    render(<ResetPasswordPage />);

    fireEvent.change(screen.getByLabelText(/Nova senha/i), {
      target: { value: "NovaSenha123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Salvar nova senha/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/reset-password", {
        token: "tok123",
        new_password: "NovaSenha123",
      }),
    );
    expect(screen.getByText(/alterada com sucesso/i)).toBeInTheDocument();
  });

  it("exibe erro quando o token é inválido/expirado", async () => {
    mockPost.mockRejectedValue(new Error("400"));
    render(<ResetPasswordPage />);

    fireEvent.change(screen.getByLabelText(/Nova senha/i), {
      target: { value: "NovaSenha123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Salvar nova senha/i }));

    await waitFor(() =>
      expect(screen.getByText(/inválido ou expirado/i)).toBeInTheDocument(),
    );
  });
});
