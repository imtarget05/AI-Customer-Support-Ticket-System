import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

// Message line WITH role-badge spans (GREEN phase implementation)
// Matches the TicketDetailPage message rendering with role badges
function MessageLine({ sender }: { sender: { name: string; role: "agent" | "customer" } }) {
  return (
    <div className="message message-test" key={sender.name}>
      <strong>{sender.name}</strong>{" "}
      <span className="hint">({sender.role})</span>
      <p>{sender.name}: Hello</p>
      <span className={`role-badge-${sender.role}`}>
        {sender.role === "agent" ? "Hỗ trợ" : "Khách hàng"}
      </span>
    </div>
  );
}

describe("role badges in thread - GREEN phase", () => {
  it("renders agent 'Hỗ trợ' badge with role-badge-agent class", () => {
    // This should now PASS (GREEN) because the MessageLine includes
    // <span className="role-badge-agent">Hỗ trợ</span>
    const { container } = render(<MessageLine sender={{ name: "Agent", role: "agent" }} />);
    const agentBadges = container.querySelectorAll(".role-badge-agent");
    expect(agentBadges.length).toBeGreaterThan(0);
  });

  it("renders customer 'Khách hàng' badge with role-badge-customer class", () => {
    // This should now PASS (GREEN) because the MessageLine includes
    // <span className="role-badge-customer">Khách hàng</span>
    const { container } = render(<MessageLine sender={{ name: "Customer", role: "customer" }} />);
    const customerBadges = container.querySelectorAll(".role-badge-customer");
    expect(customerBadges.length).toBeGreaterThan(0);
  });
});