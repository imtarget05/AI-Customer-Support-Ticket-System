import { describe, expect, it } from "vitest";
import { statusAvailability } from "../ticketUi";

describe("statusAvailability", () => {
  it("open → 5 rows, only in_progress enabled, closed disabled with reason", () => {
    const result = statusAvailability("open");
    expect(result).toHaveLength(5);

    // Only in_progress should be enabled (the allowed next status from open)
    const inProgress = result.find((r) => r.status === "in_progress");
    expect(inProgress?.enabled).toBe(true);

    // Closed should be disabled with a reason matching /terminal|trước/i
    const closed = result.find((r) => r.status === "closed");
    expect(closed?.enabled).toBe(false);
    expect(closed?.reason).toMatch(/terminal|trước/i);
  });

  it("closed → all disabled", () => {
    const result = statusAvailability("closed");
    expect(result).toHaveLength(5);
    result.forEach((r) => expect(r.enabled).toBe(false));
  });
});