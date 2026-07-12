import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "../page";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => ({
  requestLink: jest.fn(),
}));

describe("LoginPage", () => {
  it("renders the login form", () => {
    render(<LoginPage />);
    expect(screen.getByPlaceholderText("you@yourcompany.com")).toBeInTheDocument();
    expect(screen.getByText("Send sign-in link")).toBeInTheDocument();
  });

  it("submits the email and shows the dev magic link", async () => {
    (api.requestLink as jest.Mock).mockResolvedValue({
      message: "Check your work email for a sign-in link.",
      dev_magic_link: "http://localhost:3000/verify?token=abc",
    });

    render(<LoginPage />);
    const input = screen.getByPlaceholderText("you@yourcompany.com");
    fireEvent.change(input, { target: { value: "test@example.com" } });
    fireEvent.click(screen.getByText("Send sign-in link"));

    await waitFor(() => {
      expect(screen.getByText("Dev mode link:")).toBeInTheDocument();
    });
    expect(api.requestLink).toHaveBeenCalledWith("test@example.com");
  });
});
