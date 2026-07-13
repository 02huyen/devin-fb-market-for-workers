import { render, screen, waitFor } from "@testing-library/react";
import MessagesPage from "../page";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => ({
  getMe: jest.fn(),
  getConversations: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: jest.fn() }),
}));

const user = {
  id: 1,
  email: "user@example.com",
  domain: "example.com",
  company_name: "Example",
  display_name: "User",
  is_verified: true,
};

const conversation = {
  id: 5,
  listing_id: 10,
  buyer_id: 1,
  listing: { id: 10, title: "Bike", listing_type: "sell" },
  other_participant: { id: 2, display_name: "Seller", company_name: "Example" },
  unread_count: 0,
  created_at: "2026-07-13T00:00:00Z",
  updated_at: "2026-07-13T00:00:00Z",
};

describe("MessagesPage", () => {
  it("renders the empty inbox state", async () => {
    (api.getMe as jest.Mock).mockResolvedValue(user);
    (api.getConversations as jest.Mock).mockResolvedValue([]);

    render(<MessagesPage />);

    await waitFor(() => {
      expect(screen.getByText("Inbox")).toBeInTheDocument();
      expect(screen.getByText("No conversations yet.")).toBeInTheDocument();
    });
  });

  it("renders conversations with participant and listing info", async () => {
    (api.getMe as jest.Mock).mockResolvedValue(user);
    (api.getConversations as jest.Mock).mockResolvedValue([conversation]);

    render(<MessagesPage />);

    await waitFor(() => {
      expect(screen.getByText("Seller · Example")).toBeInTheDocument();
      expect(screen.getByText("Bike")).toBeInTheDocument();
    });
  });

  it("redirects to login when the user is not authenticated", async () => {
    (api.getMe as jest.Mock).mockRejectedValue(new Error("Unauthorized"));

    render(<MessagesPage />);

    await waitFor(() => {
      expect(api.getMe).toHaveBeenCalled();
    });
  });
});
