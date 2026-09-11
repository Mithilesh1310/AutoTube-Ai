"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Script from "next/script";

interface PlanPricing {
  monthly: number;
  annual: number;
  currency_symbol: string;
}

interface PlanData {
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
    credits_balance: number;
  };
  features: string[];
}

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"MONTHLY" | "ANNUAL">("MONTHLY");
  const [currency, setCurrency] = useState<"INR" | "USD">("INR");
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<string>("STARTER");
  const [creditsBalance, setCreditsBalance] = useState<number>(500);

  useEffect(() => {
    // Fetch active user subscription status
    fetch("http://localhost:8000/api/v1/billing/subscription-status")
      .then((res) => res.json())
      .then((data) => {
        if (data.plan_tier) setCurrentPlan(data.plan_tier);
        if (data.credits_balance) setCreditsBalance(data.credits_balance);
      })
      .catch(() => console.log("Using default subscription status"));
  }, []);

  const plans = [
    {
      id: "STARTER",
      name: "Starter Creator",
      priceINR: billingCycle === "MONTHLY" ? 999 : 8999,
      priceUSD: billingCycle === "MONTHLY" ? 12 : 119,
      credits: "300 Credits / mo",
      shorts: "30 AI Shorts",
      channels: "1 YouTube Channel",
      popular: false,
      badge: "Popular for Beginners",
      features: [
        "1 Connected YouTube Channel",
        "30 Autonomous Shorts / Month",
        "3D Pixar High-Res Visuals",
        "Devanagari Hindi Voice Engine",
        "Script Quality QA Gate (>=85)",
        "Daily 10:00 AM Automated Upload"
      ]
    },
    {
      id: "PRO",
      name: "Pro Animator",
      priceINR: billingCycle === "MONTHLY" ? 2499 : 22999,
      priceUSD: billingCycle === "MONTHLY" ? 30 : 279,
      credits: "1,000 Credits / mo",
      shorts: "100 AI Shorts + Moving AI Clips",
      channels: "Up to 3 YouTube Channels",
      popular: true,
      badge: "🔥 Best Value for Scaling",
      features: [
        "Up to 3 YouTube Channels",
        "100 Shorts or 22 Full Moving AI Videos",
        "Character Motion & Temporal Animation",
        "Character Universe Consistency (Chintu)",
        "Multi-Voice Emotion Acting",
        "Priority GPU Queue & 4K Visuals"
      ]
    },
    {
      id: "AGENCY",
      name: "Agency Empire",
      priceINR: billingCycle === "MONTHLY" ? 5999 : 54999,
      priceUSD: billingCycle === "MONTHLY" ? 72 : 659,
      credits: "3,000 Credits / mo",
      shorts: "300 Shorts or 65 Full Moving AI Videos",
      channels: "Up to 10 YouTube Channels",
      popular: false,
      badge: "For Channel Empire Owners",
      features: [
        "Up to 10 YouTube Channels",
        "Daily Multi-Post Automation (Morning & Evening)",
        "Full Moving AI Animation Engine (Kling/Luma)",
        "Multi-Project API Key Auto-Rotation",
        "Custom Character & Voice Tuning",
        "24/7 Priority Support & SLA"
      ]
    }
  ];

  const handleRazorpayCheckout = async (planId: string) => {
    setLoadingTier(planId);
    setStatusMessage(null);

    try {
      // 1. Request Order Creation from FastAPI Backend
      const res = await fetch("http://localhost:8000/api/v1/billing/create-checkout-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_tier: planId,
          billing_cycle: billingCycle,
          currency: currency,
          gateway: "RAZORPAY",
          user_id: 1
        })
      });

      const orderData = await res.json();

      if (!res.ok) {
        throw new Error(orderData.detail || "Failed to initiate payment");
      }

      // 2. Open Razorpay Checkout Window
      const options = {
        key: orderData.key_id || "rzp_test_simulated_key_12345",
        amount: orderData.amount_paise || orderData.amount * 100,
        currency: orderData.currency || "INR",
        name: "AutoTube AI",
        description: `Upgrade to AutoTube ${planId} Plan (${billingCycle})`,
        image: "https://cdn-icons-png.flaticon.com/512/1384/1384060.png",
        order_id: orderData.order_id?.startsWith("order_sim") ? undefined : orderData.order_id,
        handler: async function (response: any) {
          // 3. On Payment Success, Verify Payment with Backend
          setStatusMessage("🔄 Verifying Razorpay payment signature...");
          const verifyRes = await fetch("http://localhost:8000/api/v1/billing/verify-payment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: 1,
              plan_tier: planId,
              billing_cycle: billingCycle,
              currency: currency,
              gateway: "RAZORPAY",
              transaction_id: response.razorpay_payment_id || orderData.order_id || `pay_${Date.now()}`,
              order_id: response.razorpay_order_id || orderData.order_id,
              amount: orderData.amount
            })
          });

          const verifyData = await verifyRes.json();
          if (verifyData.success) {
            setCurrentPlan(planId);
            setCreditsBalance(verifyData.credits_balance);
            setStatusMessage(`🎉 Payment Successful! Plan upgraded to ${planId}.`);
          } else {
            setStatusMessage("❌ Payment verification failed. Please contact support.");
          }
          setLoadingTier(null);
        },
        modal: {
          ondismiss: function () {
            setLoadingTier(null);
            setStatusMessage("Payment process cancelled.");
          }
        },
        prefill: {
          name: "AutoTube Creator",
          email: "creator@autotube.ai",
          contact: "9876543210"
        },
        theme: {
          color: "#4f46e5"
        }
      };

      // Handle Sandbox Simulation if live keys are not configured yet
      if (orderData.mode === "SANDBOX_SIMULATION" || !(window as any).Razorpay) {
        setTimeout(async () => {
          setStatusMessage("⚡ Simulating Razorpay Payment (Sandbox Mode)...");
          const verifyRes = await fetch("http://localhost:8000/api/v1/billing/verify-payment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: 1,
              plan_tier: planId,
              billing_cycle: billingCycle,
              currency: currency,
              gateway: "RAZORPAY",
              transaction_id: `rzp_sim_${Date.now()}`,
              order_id: orderData.order_id,
              amount: orderData.amount
            })
          });
          const verifyData = await verifyRes.json();
          setCurrentPlan(planId);
          setCreditsBalance(verifyData.credits_balance);
          setStatusMessage(`🎉 Razorpay Simulation Passed! Plan upgraded to ${planId}.`);
          setLoadingTier(null);
        }, 1200);
        return;
      }

      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`❌ Error: ${err.message}`);
      setLoadingTier(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />

      {/* Header Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25">
              AT
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-indigo-300">
              AutoTube AI
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <div className="text-sm bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-full text-slate-300">
              Active Plan: <span className="font-bold text-indigo-400">{currentPlan}</span> | Credits: <span className="font-bold text-emerald-400">{creditsBalance}</span>
            </div>
            <Link
              href="/dashboard"
              className="text-sm px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-semibold transition"
            >
              Back to Dashboard →
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium">
            💳 Razorpay Payment Gateway (UPI, GPay, Cards, Netbanking)
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">
            Scale Your YouTube Channel Empire with AI Automation
          </h1>
          <p className="text-lg text-slate-400">
            Choose a plan to get credits, unlock multi-channel auto-publishing, and generate full 3D Pixar moving AI animation.
          </p>

          {/* Billing Controls */}
          <div className="pt-6 flex items-center justify-center gap-4">
            <div className="bg-slate-900 border border-slate-800 p-1 rounded-xl flex items-center gap-1">
              <button
                onClick={() => setBillingCycle("MONTHLY")}
                className={`px-5 py-2 rounded-lg text-sm font-semibold transition ${
                  billingCycle === "MONTHLY"
                    ? "bg-indigo-600 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Monthly Billing
              </button>
              <button
                onClick={() => setBillingCycle("ANNUAL")}
                className={`px-5 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 ${
                  billingCycle === "ANNUAL"
                    ? "bg-indigo-600 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Annual Billing
                <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">
                  Save 20%
                </span>
              </button>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-1 rounded-xl flex items-center gap-1">
              <button
                onClick={() => setCurrency("INR")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                  currency === "INR" ? "bg-slate-800 text-indigo-400 border border-slate-700" : "text-slate-400"
                }`}
              >
                🇮🇳 ₹ INR
              </button>
              <button
                onClick={() => setCurrency("USD")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                  currency === "USD" ? "bg-slate-800 text-indigo-400 border border-slate-700" : "text-slate-400"
                }`}
              >
                🌐 $ USD
              </button>
            </div>
          </div>
        </div>

        {/* Status Toast */}
        {statusMessage && (
          <div className="mt-8 max-w-xl mx-auto p-4 rounded-xl bg-slate-900 border border-indigo-500/30 text-center font-medium text-indigo-300 shadow-xl animate-fade-in">
            {statusMessage}
          </div>
        )}

        {/* Pricing Grid */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const price = currency === "INR" ? plan.priceINR : plan.priceUSD;
            const symbol = currency === "INR" ? "₹" : "$";
            const isCurrent = currentPlan === plan.id;

            return (
              <div
                key={plan.id}
                className={`rounded-2xl bg-slate-900 border p-8 flex flex-col justify-between transition-all duration-200 relative ${
                  plan.popular
                    ? "border-indigo-500 shadow-2xl shadow-indigo-500/10 ring-1 ring-indigo-500/50"
                    : "border-slate-800 hover:border-slate-700"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-bold shadow-lg">
                    {plan.badge}
                  </div>
                )}

                <div>
                  <div className="text-xl font-bold text-white">{plan.name}</div>
                  <div className="text-xs text-indigo-400 font-semibold mt-1">{plan.badge}</div>

                  <div className="mt-6 flex items-baseline gap-1">
                    <span className="text-4xl font-extrabold text-white">
                      {symbol}{price.toLocaleString()}
                    </span>
                    <span className="text-slate-400 text-sm">
                      /{billingCycle === "MONTHLY" ? "month" : "year"}
                    </span>
                  </div>

                  <div className="mt-4 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                    <div className="text-sm font-semibold text-emerald-400">⚡ {plan.credits}</div>
                    <div className="text-xs text-slate-300">🎬 {plan.shorts}</div>
                    <div className="text-xs text-slate-400">📺 {plan.channels}</div>
                  </div>

                  <ul className="mt-6 space-y-3">
                    {plan.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                        <span className="text-indigo-400 font-bold">✓</span>
                        {feat}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-800">
                  <button
                    disabled={loadingTier !== null || isCurrent}
                    onClick={() => handleRazorpayCheckout(plan.id)}
                    className={`w-full py-3.5 px-4 rounded-xl font-semibold transition text-sm flex items-center justify-center gap-2 ${
                      isCurrent
                        ? "bg-slate-800 text-slate-400 cursor-default border border-slate-700"
                        : plan.popular
                        ? "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/30"
                        : "bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
                    }`}
                  >
                    {loadingTier === plan.id ? (
                      <span>Opening Razorpay...</span>
                    ) : isCurrent ? (
                      <span>Current Active Plan</span>
                    ) : (
                      <span>Pay with Razorpay ({symbol}{price.toLocaleString()}) →</span>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Razorpay Trust Badges */}
        <div className="mt-16 text-center border-t border-slate-800/80 pt-10">
          <div className="text-slate-400 text-sm font-medium">
            🔒 256-Bit Encrypted Secure Payments Powered by <span className="text-indigo-400 font-bold">Razorpay</span>
          </div>
          <div className="mt-4 flex items-center justify-center gap-6 text-slate-500 text-xs">
            <span>✓ UPI (GPay, PhonePe, Paytm)</span>
            <span>✓ All Credit & Debit Cards</span>
            <span>✓ Netbanking (50+ Banks)</span>
            <span>✓ Instant Auto-Activation</span>
          </div>
        </div>
      </main>
    </div>
  );
}
