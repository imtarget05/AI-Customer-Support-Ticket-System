import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

// Contract for Task 1.2: the AI-unavailable banner must use its own error
// style (ai-unavailable), never the green success `notice` class, and expose
// role="alert" for assistive tech.
function AiUnavailableBanner({ message }: { message: string }) {
  return (
    <p data-testid="ai-unavailable" role="alert" className="ai-unavailable">
      {message}
    </p>
  );
}

describe("aiUnavailable banner", () => {
  it("renders with distinct error style and alert role", () => {
    render(<AiUnavailableBanner message="AI support is unavailable right now." />);
    const banner = screen.getByTestId("ai-unavailable");
    expect(banner).toHaveClass("ai-unavailable");
    expect(banner).not.toHaveClass("notice");
    expect(banner).toHaveRole("alert");
  });
});
