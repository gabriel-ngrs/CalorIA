import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ForgotPasswordPage from "@/app/(auth)/forgot-password/page";

const mockPost = jest.fn();

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: { post: (...args: unknown[]) => mockPost(...args) },
}));

describe("ForgotPasswordPage — fluxo de recuperação (FR-D4)", () => {
  beforeEach(() => {
    mockPost.mockReset();
  });

  it("envia o e-mail e exibe a mensagem uniforme", async () => {
    mockPost.mockResolvedValue({});
    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText(/E-mail/i), {
      target: { value: "alguem@caloria.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Enviar link/i }));

    await waitFor(() =>
      expect(
        screen.getByText(/Se o e-mail estiver cadastrado/i),
      ).toBeInTheDocument(),
    );
    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/forgot-password", {
      email: "alguem@caloria.com",
    });
  });

  it("exibe a mesma mensagem mesmo se a API falhar (não vaza existência)", async () => {
    mockPost.mockRejectedValue(new Error("erro"));
    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText(/E-mail/i), {
      target: { value: "alguem@caloria.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Enviar link/i }));

    await waitFor(() =>
      expect(
        screen.getByText(/Se o e-mail estiver cadastrado/i),
      ).toBeInTheDocument(),
    );
  });
});
