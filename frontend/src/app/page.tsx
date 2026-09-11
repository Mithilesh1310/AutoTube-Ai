'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Sparkles, Zap, ShieldCheck, Play, Tv, ArrowRight, CheckCircle2, 
  Flame, Film, Users, DollarSign, HelpCircle, ChevronDown, ChevronUp,
  Clock, Lock, Star, PlayCircle, Globe, Check, AlertCircle, RefreshCw,
  ExternalLink, Layers, ShieldAlert, Cpu, ArrowUpRight
} from 'lucide-react';
import { fetchPlans, createCheckoutSession, verifyPayment } from '@/lib/api';
import { PlansResponse, PlanItem } from '@/lib/types';

export default function SaaSMarketingLandingPage() {
  const [plansData, setPlansData] = useState<PlansResponse | null>(null);
  const [currency, setCurrency] = useState<'USD' | 'INR'>('INR');
  const [billingCycle, setBillingCycle] = useState<'MONTHLY' | 'ANNUAL'>('MONTHLY');
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  
  // Checkout Modal State
  const [checkoutPlan, setCheckoutPlan] = useState<PlanItem | null>(null);
  const [selectedGateway, setSelectedGateway] = useState<'STRIPE' | 'RAZORPAY'>('RAZORPAY');
  const [isProcessing, setIsProcessing] = useState(false);
  const [checkoutSuccess, setCheckoutSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchPlans()
      .then(data => setPlansData(data))
      .catch(err => console.error("Failed to load plans:", err));
  }, []);

  const handleOpenCheckout = (plan: PlanItem) => {
    setCheckoutPlan(plan);
    setCheckoutSuccess(null);
  };

  const handleExecutePayment = async () => {
    if (!checkoutPlan) return;
    setIsProcessing(true);
    try {
      const session = await createCheckoutSession({
        plan_tier: checkoutPlan.id,
        billing_cycle: billingCycle,
        currency: currency,
        gateway: "RAZORPAY",
        user_id: 1
      });

      if (session.checkout_url) {
        window.location.href = session.checkout_url;
        return;
      }

      const verified = await verifyPayment({
        plan_tier: checkoutPlan.id,
        billing_cycle: billingCycle,
        currency: currency,
        gateway: "RAZORPAY",
        transaction_id: session.session_id || `tx_${Date.now()}`,
        amount: session.amount,
        user_id: 1
      });

      setCheckoutSuccess(`🎉 ${verified.message} Plan valid until ${verified.valid_until}.`);
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 2000);
    } catch (err: any) {
      alert("Payment processing error: " + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const defaultPlans: Record<string, PlanItem> = {
    STARTER: {
      id: "STARTER",
      name: "Creator Starter",
      tagline: "Everything you need to launch and automate your first YouTube channel",
      popular: false,
      pricing: {
        USD: { monthly: 12, annual: 119, currency_symbol: "$" },
        INR: { monthly: 999, annual: 8999, currency_symbol: "₹" }
      },
      limits: {
        max_channels: 1,
        shorts_per_month: 30,
        long_videos_per_month: 0,
        credits_balance: 300,
        resolution: "1080p Full HD",
        voice_style: "Standard Neural Hindi",
        qa_gates: true,
        character_customization: false,
        priority_gpu: false
      },
      features: [
        "1 Connected YouTube Channel",
        "30 Autonomous Shorts / Month",
        "AI Story & Script Generation (Gemini)",
        "Automated Daily 10:00 AM Upload",
        "Built-in Script QA Gate (>=85)",
        "Standard Neural Hindi Kids Voice"
      ]
    },
    PRO: {
      id: "PRO",
      name: "Growth Pro",
      tagline: "The sweet spot for scaling 3 profitable kid story channels",
      popular: true,
      pricing: {
        USD: { monthly: 30, annual: 279, currency_symbol: "$" },
        INR: { monthly: 2499, annual: 22999, currency_symbol: "₹" }
      },
      limits: {
        max_channels: 3,
        shorts_per_month: 100,
        long_videos_per_month: 10,
        credits_balance: 1000,
        resolution: "4K Ultra HD",
        voice_style: "Multi-Speaker Emotion Voice",
        qa_gates: true,
        character_customization: true,
        priority_gpu: true
      },
      features: [
        "Up to 3 YouTube Channels",
        "100 Shorts + Moving AI Clips / Month",
        "4K Ultra HD Upscaling",
        "Consistent Character Universe (Chintu, Bholu)",
        "Multi-Voice Emotion Acting",
        "Automated Anti-Repetition Semantic Memory",
        "Priority GPU Rendering Queue"
      ]
    },
    AGENCY: {
      id: "AGENCY",
      name: "Studio Agency",
      tagline: "For production studios running automated YouTube empires",
      popular: false,
      pricing: {
        USD: { monthly: 72, annual: 659, currency_symbol: "$" },
        INR: { monthly: 5999, annual: 54999, currency_symbol: "₹" }
      },
      limits: {
        max_channels: 10,
        shorts_per_month: 300,
        long_videos_per_month: 30,
        credits_balance: 3000,
        resolution: "4K Ultra HD Cinematic",
        voice_style: "Custom Voice Cloning & Any Dialect",
        qa_gates: true,
        character_customization: true,
        priority_gpu: true
      },
      features: [
        "Up to 10 YouTube Channels",
        "Daily Multi-Post Automation (Morning & Evening)",
        "Full 3D Animation & Moving AI Engine",
        "Custom Voice Cloning & Custom Character Registry",
        "Multi-Language Expansion (Hindi, English, Spanish)",
        "Dedicated Account Manager & Fast SLA",
        "Custom Webhook & API Access"
      ]
    }
  };

  const activePlans = plansData?.plans || defaultPlans;

  const faqs = [
    {
      q: "Does AutoTube AI really run 100% automatically without any manual work?",
      a: "Yes! Once you connect your YouTube channel and configure your schedule (e.g. Daily 09:00 AM IST), our autonomous engine handles topic research, Devanagari scripting, 3D visual generation, multi-character voice acting, audio ducking, QA gates, and direct OAuth publishing automatically."
    },
    {
      q: "Is my YouTube account safe with AutoTube AI OAuth?",
      a: "Absolutely. All OAuth access and refresh tokens are encrypted at rest using bank-grade AES-128 cryptography. AutoTube uses official Google OAuth 2.0 and YouTube Data API v3 compliant endpoints with strict rate limiting."
    },
    {
      q: "Can I manage multiple channels from one account?",
      a: "Yes! On our Growth plan you can manage up to 3 channels, and on Scale up to 20 channels. Each channel has its own isolated character bible, publishing schedule, and storage."
    },
    {
      q: "What payment methods are supported?",
      a: "We support both international cards via Stripe (Visa, Mastercard, Amex) and Indian payment options via Razorpay including UPI (Google Pay, PhonePe, Paytm), NetBanking, and RuPay cards."
    },
    {
      q: "What happens if an AI provider experiences downtime?",
      a: "AutoTube AI has multi-tiered automated fallbacks. All pipeline execution progress is saved in persistent SQLite checkpoints so no job is lost."
    }
  ];

  return (
    <div className="min-h-screen bg-[#fbfbfc] text-gray-900 selection:bg-pink-200 selection:text-pink-950 font-sans">
      
      {/* 1. Polymer Floating Pill Header */}
      <div className="sticky top-4 z-50 max-w-5xl mx-auto px-4">
        <header className="bg-white/85 backdrop-blur-md border border-gray-200/80 rounded-full px-5 py-2.5 flex items-center justify-between shadow-xs transition-all">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center text-white">
              <Play className="w-3.5 h-3.5 fill-white ml-0.5" />
            </div>
            <span className="font-extrabold text-base text-gray-900 tracking-tight">AutoTube</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-gray-600">
            <a href="#features" className="hover:text-black transition">Features</a>
            <a href="#pipeline" className="hover:text-black transition">Pipeline</a>
            <a href="#characters" className="hover:text-black transition">Characters</a>
            <a href="#pricing" className="hover:text-black transition">Pricing</a>
            <a href="#faq" className="hover:text-black transition">FAQ</a>
          </nav>

          <div className="flex items-center gap-2.5">
            {/* Currency Switcher */}
            <div className="flex items-center bg-gray-100 rounded-full p-0.5 text-[11px] font-bold">
              <button
                onClick={() => setCurrency('USD')}
                className={`px-2.5 py-1 rounded-full transition ${currency === 'USD' ? 'bg-white text-black shadow-xs' : 'text-gray-500'}`}
              >
                USD
              </button>
              <button
                onClick={() => setCurrency('INR')}
                className={`px-2.5 py-1 rounded-full transition ${currency === 'INR' ? 'bg-white text-black shadow-xs' : 'text-gray-500'}`}
              >
                INR
              </button>
            </div>

            <Link
              href="/login"
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold text-gray-700 hover:text-black hover:bg-gray-100 transition hidden sm:flex items-center gap-1"
            >
              <span>Sign In</span>
            </Link>

            <Link
              href="/signup"
              className="px-4 py-1.5 rounded-full btn-polymer-black text-xs font-bold transition shadow-xs flex items-center gap-1"
            >
              <span>Start Free</span>
            </Link>
          </div>
        </header>
      </div>

      {/* 2. Hero Section (Polymer Style) */}
      <section className="pt-16 pb-12 px-4 sm:px-6 text-center max-w-5xl mx-auto space-y-6">
        {/* Top Pastel Pill Tag */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-pink-50 border border-pink-200/80 text-pink-900 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-pink-600" />
          <span>Autonomous AI YouTube Channel Studio &bull; Hands-Free Daily Publishing</span>
        </div>

        {/* Hero Main Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-gray-900 tracking-tight leading-[1.15] max-w-4xl mx-auto">
          Everything you need to automate YouTube in one place
        </h1>

        <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed">
          AutoTube AI is a powerful autonomous video production system. Generate viral 3D animated Hindi kids stories, multi-character voice acting, and auto-publish daily.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <a
            href="#pricing"
            className="px-6 py-3 rounded-full bg-pink-100 hover:bg-pink-200/80 text-pink-950 font-bold text-sm transition shadow-xs"
          >
            Start 14-day free trial
          </a>
          <Link
            href="/dashboard"
            className="px-6 py-3 rounded-full btn-polymer-black text-sm font-bold transition shadow-xs flex items-center gap-1.5"
          >
            <span>Open Studio Console</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* 3. The Signature Polymer Ambient Curved Product Frame */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-20">
        <div className="polymer-ambient-frame">
          <div className="bg-white rounded-3xl p-5 sm:p-7 shadow-sm border border-white/60 space-y-6">
            {/* Header inside mockup */}
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-black flex items-center justify-center text-white text-xs font-black">
                  AT
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900">Kids CartoonUniverse &bull; Studio</h3>
                  <p className="text-[11px] text-gray-400">Autonomous Hindi Story Channel</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Operational
                </span>
                <Link
                  href="/dashboard"
                  className="px-3 py-1 rounded-xl btn-polymer-black text-xs font-bold hidden sm:block"
                >
                  Live View &rarr;
                </Link>
              </div>
            </div>

            {/* Pipeline Step Progression */}
            <div className="p-4 rounded-2xl bg-gray-50/80 border border-gray-200/70">
              <div className="text-[11px] font-bold uppercase tracking-wider text-gray-500 mb-3">
                Automated 6-Step Production Workflow
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                {[
                  { step: '01', title: 'Topic & Idea', sub: 'Dupe Check', status: '✓ Ready' },
                  { step: '02', title: 'Devanagari Script', sub: 'QA Gate >=85', status: '✓ Verified' },
                  { step: '03', title: 'Fal AI 3D Scenes', sub: 'Character Bible', status: '3D Render' },
                  { step: '04', title: 'Hindi Voice & SFX', sub: 'EdgeTTS Ducking', status: 'Mastered' },
                  { step: '05', title: 'FFmpeg Assembly', sub: '60fps MP4', status: 'Encoded' },
                  { step: '06', title: 'YouTube OAuth', sub: 'Daily 09:00 IST', status: 'Published' },
                ].map((item, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-white border border-gray-200/80 text-left space-y-1">
                    <span className="text-[10px] font-mono font-bold text-gray-400">STEP {item.step}</span>
                    <h4 className="text-xs font-bold text-gray-900 truncate">{item.title}</h4>
                    <span className="inline-block text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Metrics & Mini Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-white border border-gray-200/80 text-left">
                <span className="text-[11px] text-gray-500 font-medium">Published Videos</span>
                <div className="text-xl font-black text-gray-900 mt-0.5">14</div>
                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded mt-1 inline-block">+100% Auto</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white border border-gray-200/80 text-left">
                <span className="text-[11px] text-gray-500 font-medium">Daily Shorts</span>
                <div className="text-xl font-black text-gray-900 mt-0.5">14</div>
                <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded mt-1 inline-block">30–60s 9:16</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white border border-gray-200/80 text-left">
                <span className="text-[11px] text-gray-500 font-medium">Active Channels</span>
                <div className="text-xl font-black text-gray-900 mt-0.5">3</div>
                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded mt-1 inline-block">Multi-OAuth</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white border border-gray-200/80 text-left">
                <span className="text-[11px] text-gray-500 font-medium">AI Credits</span>
                <div className="text-xl font-black text-gray-900 mt-0.5">5,000</div>
                <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded mt-1 inline-block">Growth Pro</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Feature Breakdown ("All in one platform") */}
      <section id="features" className="py-16 px-4 sm:px-6 max-w-5xl mx-auto space-y-12">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-black text-gray-900 tracking-tight">
            Built for creators who want passive channel growth
          </h2>
          <p className="text-sm text-gray-600 max-w-xl mx-auto">
            Traditional video creation takes 8 hours per video. AutoTube AI automates every step with zero drop in quality.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="p-6 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-xl bg-pink-50 border border-pink-200 flex items-center justify-center text-pink-700 font-bold">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-base text-gray-900">1. Research & Scripting</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Autonomous topic discovery with semantic anti-duplication memory. High-retention Devanagari Hindi scripts validated by a strict QA Gate (&gt;=85).
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 font-bold">
              <Film className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-base text-gray-900">2. Fal AI 3D & Voices</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              Fal AI Luma &amp; FLUX.1 generative scenes with consistent character bibles (Chintu, Momo). Natural EdgeTTS multi-speaker Hindi emotion voice acting.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold">
              <Tv className="w-5 h-5" />
            </div>
            <h3 className="font-extrabold text-base text-gray-900">3. Hands-Free Upload</h3>
            <p className="text-xs text-gray-600 leading-relaxed">
              60fps FFmpeg automated rendering, viral thumbnail generation, and official YouTube Data API v3 OAuth upload scheduled at your ideal daily time.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Polymer.co Inspired Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 max-w-6xl mx-auto space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <h2 className="text-4xl font-black text-gray-900 tracking-tight">
            Pricing
          </h2>
          <p className="text-sm text-gray-600">
            Simple, transparent pricing that scales with your YouTube automation needs. Start your free trial and publish videos in minutes.
          </p>

          {/* Monthly / Annual Toggle in Polymer style */}
          <div className="pt-2 flex items-center justify-center gap-2">
            <div className="inline-flex items-center bg-gray-100 p-1 rounded-full border border-gray-200 text-xs font-semibold">
              <button
                onClick={() => setBillingCycle('MONTHLY')}
                className={`px-4 py-1.5 rounded-full transition ${billingCycle === 'MONTHLY' ? 'bg-white text-black shadow-xs' : 'text-gray-500 hover:text-black'}`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('ANNUAL')}
                className={`px-4 py-1.5 rounded-full transition flex items-center gap-1.5 ${billingCycle === 'ANNUAL' ? 'bg-white text-black shadow-xs' : 'text-gray-500 hover:text-black'}`}
              >
                <span>Annual</span>
                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-pink-100 text-pink-800">
                  2 months free!
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* 3 Pricing Cards (Exact Polymer Style) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {(['STARTER', 'PRO', 'AGENCY'] as const).map((key) => {
            const plan = activePlans[key];
            const isPopular = plan.popular;
            const price = billingCycle === 'ANNUAL'
              ? Math.round(plan.pricing[currency].annual / 12)
              : plan.pricing[currency].monthly;
            const symbol = plan.pricing[currency].currency_symbol;

            return (
              <div
                key={key}
                className={`rounded-3xl bg-white border transition-all duration-200 flex flex-col justify-between p-7 relative ${
                  isPopular 
                    ? 'border-gray-900 shadow-md ring-1 ring-gray-900' 
                    : 'border-gray-200/90 shadow-xs hover:border-gray-300'
                }`}
              >
                {/* Most Popular Badge on Top */}
                {isPopular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-black text-white text-[11px] font-bold tracking-wider uppercase">
                    Most Popular
                  </div>
                )}

                <div className="space-y-5">
                  <div>
                    <h3 className="font-extrabold text-lg text-gray-900">{plan.name}</h3>
                    <p className="text-xs text-gray-500 mt-1 min-h-[32px]">{plan.tagline}</p>
                  </div>

                  {/* Price Block */}
                  <div className="pt-2 border-t border-gray-100">
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-4xl sm:text-5xl font-black text-gray-900 tracking-tight">
                        {symbol}{price.toLocaleString()}
                      </span>
                      <span className="text-xs font-semibold text-gray-500">/ month</span>
                    </div>
                    {billingCycle === 'ANNUAL' && (
                      <span className="text-[11px] text-emerald-700 font-semibold block mt-1">
                        Billed annually ({symbol}{plan.pricing[currency].annual.toLocaleString()}/yr)
                      </span>
                    )}
                  </div>

                  {/* Feature Checkmarks List */}
                  <div className="pt-2 border-t border-gray-100 space-y-3 text-xs">
                    {plan.features.map((feat, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 text-gray-600">
                        <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Primary Button */}
                <div className="pt-6 mt-6 border-t border-gray-100">
                  <button
                    onClick={() => handleOpenCheckout(plan)}
                    className="w-full py-3 rounded-xl btn-polymer-black text-xs font-bold transition shadow-xs flex items-center justify-center gap-1"
                  >
                    <span>Pay with Razorpay →</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="text-center text-xs text-gray-500">
          Instant activation via Razorpay UPI (GPay, PhonePe, Paytm), Netbanking, and Credit/Debit Cards.
        </div>

        {/* Polymer Black Callout Box */}
        <div className="rounded-3xl bg-black text-white p-8 sm:p-12 text-center max-w-4xl mx-auto space-y-4 shadow-xl">
          <h3 className="text-2xl sm:text-3xl font-black tracking-tight">
            Need more channels or enterprise multi-channel networks?
          </h3>
          <p className="text-xs sm:text-sm text-gray-400 max-w-xl mx-auto">
            If you manage more than 10 channels, require custom 3D character training, or custom API webhooks, our team can configure a dedicated cluster for you.
          </p>
          <div className="pt-2">
            <button
              onClick={() => handleOpenCheckout(activePlans.AGENCY)}
              className="px-6 py-2.5 rounded-full bg-pink-100 hover:bg-pink-200 text-pink-950 text-xs font-bold transition"
            >
              Contact Studio Sales
            </button>
          </div>
        </div>

        {/* "All plans include everything you need" Feature Grid */}
        <div className="pt-10 space-y-8">
          <div className="text-center space-y-1">
            <h3 className="text-2xl font-black text-gray-900">All plans include everything you need</h3>
            <p className="text-xs text-gray-500">Every AutoTube AI plan comes with our complete suite of autonomous agents.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-2">
              <span className="text-lg">🎬</span>
              <h4 className="font-bold text-xs text-gray-900">Automated Pipeline</h4>
              <ul className="text-[11px] text-gray-600 space-y-1">
                <li>&bull; Daily scheduled uploads</li>
                <li>&bull; 6-stage checkpoint recovery</li>
                <li>&bull; Script QA gate scoring</li>
                <li>&bull; Auto SEO &amp; tags</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-2">
              <span className="text-lg">🎨</span>
              <h4 className="font-bold text-xs text-gray-900">Character Bible</h4>
              <ul className="text-[11px] text-gray-600 space-y-1">
                <li>&bull; Chintu, Momo, Mithu</li>
                <li>&bull; Consistent faces &amp; clothes</li>
                <li>&bull; Multi-scene continuity</li>
                <li>&bull; Full HD / 4K upscaling</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-2">
              <span className="text-lg">🎙️</span>
              <h4 className="font-bold text-xs text-gray-900">Voice Acting</h4>
              <ul className="text-[11px] text-gray-600 space-y-1">
                <li>&bull; Devanagari Hindi voices</li>
                <li>&bull; Child &amp; narrator emotions</li>
                <li>&bull; Background music ducking</li>
                <li>&bull; Foley &amp; sound FX</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-2">
              <span className="text-lg">🔒</span>
              <h4 className="font-bold text-xs text-gray-900">Channel Security</h4>
              <ul className="text-[11px] text-gray-600 space-y-1">
                <li>&bull; AES-128 token encryption</li>
                <li>&bull; YouTube v3 rate limiting</li>
                <li>&bull; Emergency stop lock</li>
                <li>&bull; Isolated channel storage</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 6. FAQ Section */}
      <section id="faq" className="py-16 px-4 sm:px-6 max-w-3xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-black text-gray-900 tracking-tight">Frequently Asked Questions</h2>
          <p className="text-xs text-gray-500">Everything you need to know about AutoTube AI autonomous operation.</p>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <div
              key={i}
              className="rounded-2xl bg-white border border-gray-200/80 overflow-hidden shadow-xs"
            >
              <button
                onClick={() => setActiveFaq(activeFaq === i ? null : i)}
                className="w-full text-left p-5 flex items-center justify-between font-bold text-sm text-gray-900"
              >
                <span>{faq.q}</span>
                {activeFaq === i ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
              </button>
              {activeFaq === i && (
                <div className="px-5 pb-5 text-xs text-gray-600 leading-relaxed border-t border-gray-100 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 7. Bottom CTA Ambient Box (Signature Polymer Look) */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-20">
        <div className="polymer-ambient-frame text-center p-10 sm:p-14 space-y-4">
          <h2 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight">
            Start automating your YouTube channels today
          </h2>
          <p className="text-xs sm:text-sm text-gray-700 max-w-md mx-auto">
            Scale your audience and income with 3D Pixar visuals and hands-free daily uploads.
          </p>
          <div className="pt-2">
            <a
              href="#pricing"
              className="px-8 py-3.5 rounded-full btn-polymer-black text-sm font-bold shadow-md inline-block"
            >
              Select Your Plan Now
            </a>
          </div>
        </div>
      </section>

      {/* 8. Solid Black Polymer Footer */}
      <footer className="bg-black text-white pt-16 pb-12 px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-5 gap-10 border-b border-white/10 pb-12">
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-black">
                <Play className="w-3.5 h-3.5 fill-black ml-0.5" />
              </div>
              <span className="font-extrabold text-lg text-white tracking-tight">AutoTube AI</span>
            </div>
            <p className="text-xs text-gray-400 max-w-sm leading-relaxed">
              AutoTube AI helps you automate and scale profitable YouTube channels with 3D Pixar visuals, emotional Devanagari storytelling, and scheduled daily uploads.
            </p>
            <div className="pt-2 flex items-center gap-3 text-xs">
              <Link href="/login" className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white font-semibold transition">
                Creator Sign In
              </Link>
              <Link href="/signup" className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition">
                Get Started
              </Link>
            </div>
            <p className="text-[11px] text-gray-500 pt-2">
              &copy; {new Date().getFullYear()} AutoTube AI Technologies. All rights reserved.
            </p>
          </div>

          <div className="space-y-2 text-xs">
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">Product</h4>
            <p><a href="#pipeline" className="text-gray-400 hover:text-white transition">Video Pipeline</a></p>
            <p><a href="#characters" className="text-gray-400 hover:text-white transition">Character Bible</a></p>
            <p><a href="#pricing" className="text-gray-400 hover:text-white transition">Pricing Plans</a></p>
            <p><Link href="/dashboard" className="text-gray-400 hover:text-white transition">Studio Console</Link></p>
          </div>

          <div className="space-y-2 text-xs">
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">Legal &amp; Policies</h4>
            <p><Link href="/privacy" className="text-gray-400 hover:text-white transition">Privacy Policy</Link></p>
            <p><Link href="/terms" className="text-gray-400 hover:text-white transition">Terms of Service</Link></p>
            <p><Link href="/refund" className="text-gray-400 hover:text-white transition">Refund &amp; Cancellation</Link></p>
            <p><Link href="/contact" className="text-gray-400 hover:text-white transition">Contact &amp; Support</Link></p>
          </div>

          <div className="space-y-2 text-xs">
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">Payment &amp; Trust</h4>
            <p className="text-gray-400">Razorpay India (UPI, GPay, PhonePe)</p>
            <p className="text-gray-400">All Credit &amp; Debit Cards</p>
            <p className="text-gray-400">Google OAuth 2.0 Encrypted</p>
            <p className="text-gray-400">AES-256 Fernet Cryptography</p>
          </div>
        </div>
      </footer>

      {/* 9. Checkout & Subscription Modal */}
      {checkoutPlan && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white border border-gray-200 rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
                  Razorpay Secure Checkout
                </span>
                <h3 className="font-extrabold text-lg text-gray-900 mt-1">Activate {checkoutPlan.name} Plan</h3>
              </div>
              <button
                onClick={() => setCheckoutPlan(null)}
                className="w-8 h-8 rounded-full bg-gray-100 text-gray-500 hover:text-black flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            {/* Price Confirmation */}
            <div className="p-4 rounded-2xl bg-gray-50 border border-gray-200/80 flex items-center justify-between">
              <div>
                <span className="text-xs text-gray-500 font-medium">Selected Tier &bull; {billingCycle}</span>
                <div className="text-2xl font-black text-gray-900">
                  {checkoutPlan.pricing[currency].currency_symbol}
                  {billingCycle === 'ANNUAL'
                    ? checkoutPlan.pricing[currency].annual.toLocaleString()
                    : checkoutPlan.pricing[currency].monthly.toLocaleString()}
                  <span className="text-xs font-normal text-gray-500">
                    {billingCycle === 'ANNUAL' ? '/year' : '/month'}
                  </span>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                Razorpay Instant Activation
              </span>
            </div>

            {/* Gateway Info */}
            <div className="p-3 rounded-xl bg-slate-900 text-white text-xs font-semibold flex items-center gap-2">
              <span className="text-emerald-400 font-bold">💳 Payment Gateway:</span>
              <span>Razorpay (UPI, GPay, Paytm, Cards, Netbanking)</span>
            </div>

            {checkoutSuccess ? (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-bold text-center animate-in fade-in">
                {checkoutSuccess} Redirecting to Studio...
              </div>
            ) : (
              <button
                onClick={handleExecutePayment}
                disabled={isProcessing}
                className="w-full py-3.5 rounded-xl btn-polymer-black text-xs font-bold transition shadow-sm flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Lock className="w-4 h-4" />
                )}
                <span>
                  {isProcessing ? "Processing Razorpay Activation..." : `Proceed to Razorpay Checkout →`}
                </span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
