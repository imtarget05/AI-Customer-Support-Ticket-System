import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
describe("smoke", () => {
  it("renders hello", () => {
    render(<p data-testid="smoke">hello</p>);
    expect(screen.getByTestId("smoke")).toHaveTextContent("hello");
  });
});
