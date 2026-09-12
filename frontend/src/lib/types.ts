export type VisualMode = 'IMAGE_MOTION' | 'FULL_ANIMATION' | 'HYBRID' | 'AUTO';

export interface ChannelAutomationProfile {
  niche: string;
  sub_niche?: string;
  language: string;
  target_audience: string;
  visual_mode: VisualMode;
  video_format: 'SHORT' | 'LONG' | 'BOTH';
  videos_per_day: number;
  publish_times: string[];
  automation_enabled: boolean;
  auto_publish: boolean;
  voice_style: string;
  character_universe: string;
}

export interface YouTubeChannelItem {
  id: number;
  channel_name: string;
  youtube_channel_id?: string;
  description?: string;
  channel_thumbnail?: string;
  is_connected: boolean;
  created_at: string;
  profile?: ChannelAutomationProfile;
}

export interface DashboardSummary {
  agent_status: string;
  agent_enabled: boolean;
  global_emergency_stop?: boolean;
  total_videos: number;
  shorts_generated: number;
  long_videos_generated: number;
  total_connected_channels: number;
  channel_connected: boolean;
  channel_name: string;
  channel_id?: number | null;
  publish_mode: string;
  is_job_active?: boolean;
  latest_job: {
    id: string | null;
    status: string;
    current_step: string;
    visual_mode?: string;
    checkpoint_stage?: string;
    progress: number;
    created_at: string | null;
  } | null;
}

export interface VideoRecord {
  id: number;
  channel_id?: number;
  title: string;
  video_type: 'SHORT' | 'LONG';
  visual_mode: VisualMode;
  status: string;
  publish_mode: string;
  video_path?: string;
  thumbnail_path?: string;
  youtube_video_id?: string;
  youtube_url?: string;
  qa_passed?: boolean;
  created_at: string;
}

export interface CharacterItem {
  character_id: string;
  name: string;
  species: string;
  personality: string;
  physical_description: string;
  clothing: string;
  color_palette: string;
  visual_prompt_base: string;
  negative_prompt: string;
  voice_config: any;
  master_ref_image?: string;
}

export interface JobRecord {
  id: string;
  channel_id?: number;
  job_type: string;
  visual_mode: VisualMode;
  status: string;
  checkpoint_stage: string;
  current_step: string;
  progress_percentage: number;
  estimated_cost?: number;
  actual_cost?: number;
  error_message?: string;
  created_at: string;
}

export interface JobLogItem {
  id: number;
  job_id: string;
  agent_name: string;
  log_level: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  message: string;
  timestamp: string;
}

export interface YouTubeVideoPerformance {
  video_id: string;
  title: string;
  thumbnail_url: string;
  views: number;
  likes: number;
  comments: number;
  published_at: string;
  youtube_url: string;
}

export interface AnalyticsSummary {
  channel_title: string;
  channel_custom_url: string;
  channel_avatar: string;
  is_live_data: boolean;
  total_views: number;
  total_subscribers: number;
  total_videos_youtube: number;
  total_likes: number;
  total_comments: number;
  total_local_videos: number;
  shorts_count: number;
  longs_count: number;
  pipeline_success_rate: number;
  top_videos: YouTubeVideoPerformance[];
  learning_insights: {
    best_topics: string[];
    worst_topics: string[];
    retention_insights: string;
    recommendations: string[];
  };
}

export interface EmergencyStatus {
  global_emergency_stop: boolean;
  running_jobs_count: number;
  running_jobs: Array<{
    id: string;
    current_step: string;
    job_type: string;
    visual_mode: string;
    progress_percentage: number;
    created_at: string;
  }>;
  system_status: 'LOCKED' | 'BUSY' | 'NORMAL';
}

export interface AdminSummary {
  total_users: number;
  total_channels: number;
  total_jobs: number;
  queue_depth: number;
  completed_jobs: number;
  failed_jobs: number;
  failure_rate_pct: number;
  total_spend_usd: number;
  total_credits_used: number;
  global_emergency_stop: boolean;
  visual_mode_breakdown: Record<string, number>;
  providers_status: Record<string, any>;
}

export interface PlanPricing {
  monthly: number;
  annual: number;
  currency_symbol: string;
}

export interface PlanItem {
  id: string;
  name: string;
  tagline: string;
  popular: boolean;
  pricing: {
    USD: PlanPricing;
    INR: PlanPricing;
  };
  limits: {
    max_channels: number;
    shorts_per_month: number;
    long_videos_per_month: number;
    credits_balance: number;
    resolution: string;
    voice_style: string;
    qa_gates: boolean;
    character_customization: boolean;
    priority_gpu: boolean;
  };
  features: string[];
}

export interface PlansResponse {
  plans: Record<string, PlanItem>;
  supported_currencies: string[];
  gateways: {
    stripe_enabled: boolean;
    razorpay_enabled: boolean;
    sandbox_mode: boolean;
  };
}

export interface SubscriptionStatus {
  plan_tier: string;
  plan_name: string;
  subscription_status: string;
  credits_balance: number;
  renewal_date: string;
  limits: PlanItem['limits'];
  usage: {
    channels_used: number;
    max_channels: number;
    remaining_channels: number;
  };
}

export interface UserProfile {
  user_id: number;
  username: string;
  email: string;
  is_admin: boolean;
  plan_tier: string;
  subscription_status: string;
  credits_balance: number;
  daily_credit_limit: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  email: string;
  plan_tier: string;
  credits_balance: number;
}

