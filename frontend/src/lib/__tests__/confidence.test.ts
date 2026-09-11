import { describe, expect, it } from "vitest";
import { describeConfidence } from "../ticketUi";

describe("describeConfidence", () => {
  it("v < 0.32 → low", () => {
    const result = describeConfidence(0.32);
    expect(result.level).toBe("low");
    expect(result.text).toContain("Thấp");
    expect(result.pct).toBe(32);
  });

  it("0.65 → medium with Vietnamese explanation", () => {
    const result = describeConfidence(0.65);
    expect(result.level).toBe("medium");
    expect(result.text).toContain("Trung bình");
    expect(result.pct).toBe(65);
  });

  it("0.91 → high", () => {
    const result = describeConfidence(0.91);
    expect(result.level).toBe("high");
    expect(result.text).toContain("Cao");
    expect(result.pct).toBe(91);
  });

  it("null → Chưa có đánh giá AI", () => {
    const result = describeConfidence(null);
    expect(result.level).toBe("low");
    expect(result.text).toBe("Chưa có đánh giá AI");
    expect(result.pct).toBe(0);
  });
});