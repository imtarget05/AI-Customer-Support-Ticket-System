import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

function ReplyActions({ draft, onUse, onDismiss }: { draft: string; onUse: (t: string) => void; onDismiss: () => void }) {
  return (
    <div>
      <button onClick={() => onUse(draft)}>Chèn gợi ý vào ô trả lời</button>
      <button style={{ marginLeft: "8px" }} onClick={onDismiss}>Bỏ qua gợi ý</button>
    </div>
  );
}

afterEach(() => cleanup());

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
    const useBtn = screen.getAllByRole("button", { name: /Chèn gợi ý/ })[0];
    useBtn.click();
    expect(captured).toBe("hello");
  });

  it("click 'Bỏ qua gợi ý' calls onDismiss once", () => {
    let callCount = 0;
    const onDismiss = () => { callCount += 1; };
    const onUse = () => { /* no-op */ };
    render(<ReplyActions draft="hello" onUse={onUse} onDismiss={onDismiss} />);
    const dismissBtn = screen.getAllByRole("button", { name: /Bỏ qua/ })[0];
    dismissBtn.click();
    expect(callCount).toBe(1);
  });
});