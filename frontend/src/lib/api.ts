import { 
  DashboardSummary, 
  VideoRecord, 
  CharacterItem, 
  JobRecord, 
  JobLogItem, 
  AnalyticsSummary, 
  YouTubeChannelItem,
  EmergencyStatus,
  VisualMode,
  PlansResponse,
  SubscriptionStatus,
  UserProfile,
  AuthResponse
} from './types';

export const getApiBase = () => {
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/v1`;
  }
  const rawApi = process.env.NEXT_PUBLIC_API_URL || 'https://autotube.co.in/api/v1';
  return rawApi.endsWith('/api/v1') ? rawApi : `${rawApi.replace(/\/+$/, '')}/api/v1`;
};

const API_BASE = getApiBase();

// --- Token & Session Management ---
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('autotube_token');
}

export function setAuthToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('autotube_token', token);
  }
}

export function removeAuthToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('autotube_token');
    localStorage.removeItem('autotube_user');
  }
}

export function getStoredUser(): UserProfile | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem('autotube_user');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: any) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('autotube_user', JSON.stringify(user));
  }
}

export function getAuthHeaders(customHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...customHeaders };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// --- Auth Endpoints ---
export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed. Please check your credentials.');
  }
  const data: AuthResponse = await res.json();
  setAuthToken(data.access_token);
  setStoredUser({
    user_id: data.user_id,
    username: data.username,
    email: data.email,
    plan_tier: data.plan_tier,
    credits_balance: data.credits_balance
  });
  return data;
}

export async function registerUser(username: string, email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed. Please check your details.');
  }
  const data: AuthResponse = await res.json();
  setAuthToken(data.access_token);
  setStoredUser({
    user_id: data.user_id,
    username: data.username,
    email: data.email,
    plan_tier: data.plan_tier,
    credits_balance: data.credits_balance
  });
  return data;
}

export async function googleLoginUser(credential: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Google sign-in failed.');
  }
  const data: AuthResponse = await res.json();
  setAuthToken(data.access_token);
  setStoredUser({
    user_id: data.user_id,
    username: data.username,
    email: data.email,
    plan_tier: data.plan_tier,
    credits_balance: data.credits_balance
  });
  return data;
}

export async function fetchMyProfile(): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
    cache: 'no-store'
  });
  if (!res.ok) throw new Error('Failed to fetch user profile');
  const user: UserProfile = await res.json();
  setStoredUser(user);
  return user;
}

export function logoutUser() {
  removeAuthToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

// --- Data Endpoints (All Protected with Auth Headers) ---
export async function fetchDashboardSummary(channelId?: number): Promise<DashboardSummary> {
  const url = channelId ? `${API_BASE}/dashboard?channel_id=${channelId}` : `${API_BASE}/dashboard`;
  const res = await fetch(url, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchVideos(channelId?: number, visualMode?: VisualMode): Promise<VideoRecord[]> {
  const params = new URLSearchParams();
  if (channelId) params.append('channel_id', channelId.toString());
  if (visualMode) params.append('visual_mode', visualMode);
  const url = params.toString() ? `${API_BASE}/videos?${params.toString()}` : `${API_BASE}/videos`;
  const res = await fetch(url, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch videos');
  return res.json();
}

export async function fetchCharacters(): Promise<CharacterItem[]> {
  const res = await fetch(`${API_BASE}/characters`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch characters');
  return res.json();
}

export async function fetchJobs(channelId?: number): Promise<JobRecord[]> {
  const url = channelId ? `${API_BASE}/jobs?channel_id=${channelId}` : `${API_BASE}/jobs`;
  const res = await fetch(url, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch jobs');
  return res.json();
}

export async function retryJob(jobId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to retry job from checkpoint');
  return res.json();
}

export async function fetchLogs(jobId?: string): Promise<JobLogItem[]> {
  const url = jobId ? `${API_BASE}/logs?job_id=${jobId}` : `${API_BASE}/logs`;
  const res = await fetch(url, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch logs');
  return res.json();
}

export async function fetchAnalytics(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_BASE}/analytics`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

export async function fetchSettings(): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/settings`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch settings');
  return res.json();
}

export async function updateSettings(settings: Record<string, string>): Promise<any> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error('Failed to update settings');
  return res.json();
}

export async function fetchChannels(): Promise<YouTubeChannelItem[]> {
  const res = await fetch(`${API_BASE}/channels`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch channels');
  return res.json();
}

export async function createChannel(data: {
  channel_name: string;
  niche: string;
  visual_mode: string;
  video_format?: string;
  videos_per_day?: number;
  publish_times?: string[];
}): Promise<any> {
  const res = await fetch(`${API_BASE}/channels`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create channel');
  }
  return res.json();
}

export async function updateChannelAutomation(channelId: number, data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/channels/${channelId}/automation`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update channel automation profile');
  }
  return res.json();
}

export async function toggleChannelAutomation(channelId: number, action: 'pause' | 'resume'): Promise<any> {
  const res = await fetch(`${API_BASE}/channels/${channelId}/${action}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to ${action} channel automation`);
  return res.json();
}

export async function deleteChannel(channelId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/channels/${channelId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete channel');
  return res.json();
}

export async function fetchYouTubeAuthUrl(): Promise<{ status: string; auth_url?: string }> {
  const res = await fetch(`${API_BASE}/youtube/auth-url`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch YouTube auth url');
  return res.json();
}

export async function fetchYouTubeChannel(): Promise<{ connected: boolean; channel_name?: string; channel_id?: string }> {
  const res = await fetch(`${API_BASE}/youtube/channel`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch YouTube channel info');
  return res.json();
}

export async function disconnectYouTubeChannel(): Promise<any> {
  const res = await fetch(`${API_BASE}/youtube/disconnect`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to disconnect YouTube channel');
  return res.json();
}

export async function fetchEmergencyStatus(): Promise<EmergencyStatus> {
  const res = await fetch(`${API_BASE}/emergency/status`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch emergency status');
  return res.json();
}

export async function triggerWorkflow(
  videoType: 'DAILY_WORKFLOW' | 'SHORT' | 'LONG',
  visualMode: VisualMode = 'IMAGE_MOTION',
  channelId?: number
): Promise<{ status: string; job_id: string; visual_mode: string }> {
  const res = await fetch(`${API_BASE}/workflow/run`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ 
      video_type: videoType,
      visual_mode: visualMode,
      channel_id: channelId
    }),
  });
  if (!res.ok) throw new Error('Failed to trigger workflow');
  return res.json();
}

export async function fetchPlans(): Promise<PlansResponse> {
  const res = await fetch(`${API_BASE}/billing/plans`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch billing plans');
  return res.json();
}

export async function createCheckoutSession(payload: {
  plan_tier: string;
  billing_cycle: 'MONTHLY' | 'ANNUAL';
  currency: 'USD' | 'INR';
  gateway: 'STRIPE' | 'RAZORPAY' | 'UPI' | 'DIRECT_UPI';
  user_id?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/billing/create-checkout-session`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create checkout session');
  return res.json();
}

export async function verifyPayment(payload: {
  plan_tier: string;
  billing_cycle: 'MONTHLY' | 'ANNUAL';
  currency: 'USD' | 'INR';
  gateway: 'STRIPE' | 'RAZORPAY' | 'UPI' | 'DIRECT_UPI';
  transaction_id: string;
  order_id?: string;
  amount: number;
  user_id?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/billing/verify-payment`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to verify payment');
  return res.json();
}

export async function fetchSubscriptionStatus(userId: number = 1): Promise<SubscriptionStatus> {
  const res = await fetch(`${API_BASE}/billing/subscription-status?user_id=${userId}`, { headers: getAuthHeaders(), cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch subscription status');
  return res.json();
}
