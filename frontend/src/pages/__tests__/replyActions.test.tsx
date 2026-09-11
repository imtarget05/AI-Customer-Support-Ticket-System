import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

function ReplyActions({ draft, onUse, onDismiss }: { draft: string; onUse: (t: string) => void; onDismiss: () => void }) {
  return (
    <div>
      <button>Chèn gợi ý vào ô trả lời</button>
      <button style={{ marginLeft: "8px" }}>Bỏ qua gợi ý</button>
    </div>
  );
}

describe("reply-actions cluster", () => {
  it("renders two buttons", () => {
    render(<ReplyActions draft="hello" onUse={(() => { })} onDismiss={(() => { })} />);
    const buttons = screen.getAllByRole("button", { name: /Chèn gợi ý|Bỏ qua/ });
    expect(buttons).toHaveLength(2);
  });

  it("click 'Chèn gợi ý vào ô trả lời' calls onUse with draft", () => {
    let captured: string | null = null;
    const onUse = (t: string) => { captured = t; };
    const onDismiss = () => { /* no-op */ };
    render(<ReplyActions draft="hello" onUse={onUse} onDismiss={onDismiss} />);
    const useBtn = screen.getByRole("button", { name: /Chèn gợi ý/ });
    useBtn.click();
    expect(captured).toBe("hello");
  });

  it("click 'Bỏ qua gợi ý' calls onDismiss once", () => {
    let callCount = 0;
    const onDismiss = () => { callCount += 1; };
    const onUse = () => { /* no-op */ };
    render(<ReplyActions draft="hello" onUse={onUse} onDismiss={onDismiss} />);
    const dismissBtn = screen.getByRole("button", { name: /Bỏ qua/ });
    dismissBtn.click();
    expect(callCount).toBe(1);
  });
});