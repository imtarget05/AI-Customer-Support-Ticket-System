import type { TicketStatus } from "../types";

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