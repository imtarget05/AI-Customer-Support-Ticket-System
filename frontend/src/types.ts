export type Role = "customer" | "agent";
export type TicketStatus = "open" | "in_progress" | "waiting" | "resolved" | "closed";
export type TicketPriority = "low" | "normal" | "high" | "urgent";
export type TicketCategory =
  | "unknown"
  | "authentication"
  | "payment"
  | "refund"
  | "technical"
  | "other";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
}

export interface Message {
  id: number;
  sender: User;
  content: string;
  created_at: string;
  email_status?: string;  // sent | skipped_no_customer | skipped_no_config | failed_logged
}

export interface Ticket {
  id: number;
  subject: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  ai_summary: string | null;
  ai_confidence: number | null;
  customer: User;
  created_at: string;
  updated_at: string;
}

export interface TicketDetail extends Ticket {
  messages: Message[];
}

export interface TicketPage {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardStats {
  total: number;
  by_status: Record<TicketStatus, number>;
  by_priority: Record<TicketPriority, number>;
  by_category: Record<TicketCategory, number>;
  high_priority_open: number;
}

export interface Suggestion {
  response: string;
  based_on_similar: number[];
}

export interface SimilarTicket {
  ticket_id: number;
  subject: string;
  status: TicketStatus;
  similarity: number;
}

export const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Open",
  in_progress: "In Progress",
  waiting: "Waiting",
  resolved: "Resolved",
  closed: "Closed",
};

export const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
  urgent: "Urgent",
};

export const CATEGORY_LABELS: Record<TicketCategory, string> = {
  unknown: "Unknown",
  authentication: "Authentication",
  payment: "Payment",
  refund: "Refund",
  technical: "Technical",
  other: "Other",
};
