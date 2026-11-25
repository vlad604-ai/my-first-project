export interface Category {
  id: number; slug: string; parent_id: number | null; names: Record<string, string>; icon: string | null;
  keywords: string[]; default_work_mode: string; supports_quotes: boolean; is_health: boolean; is_active: boolean;
  sort_order: number; children: Category[];
}
export interface Service {
  id: number; name: string; description: string | null; duration_min: number; price_cents: number | null;
  price_type: string; location: string; is_active: boolean;
}
export interface Slot { start: string; end: string; freed: boolean }
export interface ProSummary {
  id: number; business_name: string; slug: string; description: string | null; category_id: number; work_mode: string;
  city: string | null; postal_code: string | null; lat: number | null; lon: number | null; service_radius_km: number;
  is_verified: boolean; rating_avg: number; rating_count: number; completed_count: number; logo_url: string | null;
  accepts_quotes: boolean;
}
export interface ProDetail extends ProSummary {
  address: string | null; phone: string | null; website: string | null; specialties: string[]; services: Service[];
  timezone: string; status: string; hours: Record<string, string[]>; photos: { id: number; url: string | null }[];
}
export interface SearchResult {
  professional: ProSummary; distance_km: number | null; travel_minutes: number | null;
  reference_service: Service | null; min_price_cents: number | null; next_slots: Slot[]; on_duty: boolean;
  sponsored: boolean; score: number;
}
export interface SearchResponse { total: number; results: SearchResult[]; understood?: Record<string, unknown>; summary?: string }
export interface Booking {
  id: string; reference: string; professional_id: number; service_id: number | null; service_name: string | null;
  start_at: string; end_at: string; status: string; location: string; address: string | null; price_cents: number | null;
  is_urgent: boolean; client_note: string | null; cancel_reason: string | null; created_at: string;
}
export interface Review {
  id: number; booking_id: string; professional_id: number; rating: number; comment: string | null; status: string;
  moderation_reason: string | null; pro_reply: string | null; created_at: string;
}
export interface User {
  id: number; telegram_id: number | null; username: string | null; first_name: string | null; last_name: string | null;
  language: string; is_admin: boolean; is_banned: boolean; created_at: string;
}
export interface Page<T> { items: T[]; total: number }
