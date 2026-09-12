import { fireEvent, render, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SupportPage from "./SupportPage";
import { AuthContext } from "../App";
import { api } from "../lib/api";
import type { Ticket, User } from "../types";

vi.mock("../lib/api", () => ({
  api: vi.fn(),
  getToken: () => null,
  setToken: () => {},
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

const testUser: User = { id: 1, name: "Test", email: "test@test.com", role: "customer" };
const authValue = { user: testUser, setUser: () => {}, logout: () => {} };

function renderSupportPage() {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <SupportPage />
      </AuthContext.Provider>
    </MemoryRouter>
  );
}

describe("SupportPage", () => {
  it("renders initial form container", () => {
    const { container } = renderSupportPage();
    const html = container?.innerHTML || "";
    // Check that the form section exists in initial render
    expect(html).toContain("Submit a Ticket");
  });

  it("keeps form after create with history panel", async () => {
    const mockTicket: Ticket = {
      id: 101,
      subject: "Test subject",
      description: "Test description that is long enough",
      category: "unknown",
      priority: "normal",
      status: "open",
      ai_summary: null,
      ai_confidence: null,
      customer: testUser,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    vi.mocked(api).mockResolvedValue(mockTicket);

    const { container } = renderSupportPage();
    const scope = within(container);

    // Fill form and submit (scoped to this render's container)
    const subjectInput = scope.getByLabelText("Subject") as HTMLInputElement;
    const descriptionInput = scope.getByLabelText("Description") as HTMLInputElement;
    fireEvent.change(subjectInput, { target: { value: "Test subject" } });
    fireEvent.change(descriptionInput, { target: { value: "Test description that is long enough" } });
    const form = container.querySelector("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form as HTMLFormElement);

    // Wait for success card
    await scope.findByTestId("success-card");
    // Form should still exist
    expect(scope.getByLabelText("Subject")).toBeInTheDocument();
    // History panel should exist
    expect(container.querySelector("[data-testid='history-panel']")).not.toBeNull();
  });
});
