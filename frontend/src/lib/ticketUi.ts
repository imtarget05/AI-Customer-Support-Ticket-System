import type { TicketStatus } from "../types";

// Độ tin cậy AI: level + text tiếng Việt
export interface ConfidenceDisplay {
  pct: number;
  level: "low" | "medium" | "high";
  text: string;
}

/**
 * Chuyển đổi giá trị độ tin cậy (0-1) thành thông ngữ tiếng Việt.
 * - v < 0.5: low, cần kiểm tra kỹ
 * - 0.5 ≤ v < 0.8: medium, tham khảo nhưng kiểm tra lại
 * - v ≥ 0.8: high, vẫn cần xác minh
 * - v == null: Chưa có đánh giá AI
 */
export function describeConfidence(v: number | null): ConfidenceDisplay {
  if (v === null) {
    return { pct: 0, level: "low", text: "Chưa có đánh giá AI" };
  }
  const pct = Math.round(v * 100);
  if (v < 0.5) {
    return {
      pct,
      level: "low",
      text: `Độ tin cậy: ${pct}% (Thấp — AI chưa chắc, cần đọc kỹ ticket trước khi hành động)`,
    };
  }
  if (v < 0.8) {
    return {
      pct,
      level: "medium",
      text: `Độ tin cậy: ${pct}% (Trung bình — tham khảo, nên kiểm tra lại)`,
    };
  }
  return {
    pct,
    level: "high",
    text: `Độ tin cậy: ${pct}% (Cao — vẫn cần xác minh trước khi trả lời khách)`,
  };
}

// Full status lifecycle flow
export const STATUS_FLOW: TicketStatus[] = [
  "open",
  "in_progress",
  "waiting",
  "resolved",
  "closed",
];

// Valid next statuses per the backend state machine
const NEXT_MAP: Record<TicketStatus, TicketStatus[]> = {
  open: ["in_progress"],
  in_progress: ["waiting", "resolved"],
  waiting: ["in_progress"],
  resolved: ["closed"],
  closed: [],
};

// Vietnamese-labeled status names (used for tooltips)
export const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Mở",
  in_progress: "Đang xử lý",
  waiting: "Chờ phản hồi",
  resolved: "Đã khắc phục",
  closed: "Đã đóng",
};

/**
 * Returns the availability state for each status in the flow given the
 * current ticket status. The current status is marked `current: true` and
 * is not presented as a transition button.
 *
 * @param status Current ticket status
 * @returns Array of { status, enabled, reason, current }
 */
export function statusAvailability(status: TicketStatus): Array<{
  status: TicketStatus;
  enabled: boolean;
  reason: string | null;
  current: boolean;
}> {
  const canTransitionTo = NEXT_MAP[status] ?? [];

  return STATUS_FLOW.map((s) => {
    const current = s === status;
    const enabled = !current && canTransitionTo.includes(s);
    let reason: string | null = null;

    if (current) {
      // Current status has no reason; it is already the active state
      reason = null;
    } else if (!enabled) {
      // Disabled status – provide a Vietnamese tooltip reason
      if (s === "closed") {
        reason = "Terminal";
      } else if (status === "open") {
        reason = "Terminal";
      } else {
        reason = `${STATUS_LABELS[s]} không thể chuyển`;
      }
    }

    return { status: s, enabled, reason, current };
  });
}