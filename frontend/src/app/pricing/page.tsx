'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { createCheckoutSession, verifyPayment } from '@/lib/api';
import {
  Zap,
  CheckCircle2,
  ShieldCheck,
  CreditCard,
  Copy,
  Check,
  Smartphone,
  X
} from 'lucide-react';

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'MONTHLY' | 'ANNUAL'>('MONTHLY');
  const [currency, setCurrency] = useState<'INR' | 'USD'>('INR');
  const [currentPlan, setCurrentPlan] = useState<string>('STARTER');
  const [creditsBalance, setCreditsBalance] = useState<number>(500);

  // Modal State
  const [checkoutPlan, setCheckoutPlan] = useState<any | null>(null);
  const [selectedGateway, setSelectedGateway] = useState<'UPI' | 'RAZORPAY'>('UPI');
  const [upiData, setUpiData] = useState<any | null>(null);
  const [utrNumber, setUtrNumber] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [checkoutSuccess, setCheckoutSuccess] = useState<string | null>(null);
  const [copiedVpa, setCopiedVpa] = useState(false);

  useEffect(() => {
    fetch('/api/v1/billing/subscription-status')
      .then((res) => res.json())
      .then((data) => {
        if (data.plan_tier) setCurrentPlan(data.plan_tier);
        if (data.credits_balance) setCreditsBalance(data.credits_balance);
      })
      .catch(() => console.log('Using default subscription status'));
  }, []);

  const handleOpenCheckout = async (plan: any) => {
    setCheckoutPlan(plan);
    setCheckoutSuccess(null);
    setSelectedGateway('UPI');
    setIsProcessing(true);
    try {
      const session = await createCheckoutSession({
        plan_tier: plan.id,
        billing_cycle: billingCycle,
        currency: currency,
        gateway: 'UPI' as any,
        user_id: 1
      });
      setUpiData(session);
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSwitchGateway = async (gateway: 'UPI' | 'RAZORPAY') => {
    setSelectedGateway(gateway);
    if (gateway === 'UPI' && !upiData && checkoutPlan) {
      setIsProcessing(true);
      try {
        const session = await createCheckoutSession({
          plan_tier: checkoutPlan.id,
          billing_cycle: billingCycle,
          currency: currency,
          gateway: 'UPI' as any,
          user_id: 1
        });
        setUpiData(session);
      } catch (err) {
        console.error(err);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleExecutePayment = async () => {
    if (!checkoutPlan) return;
    setIsProcessing(true);
    try {
      if (selectedGateway === 'UPI') {
        const txnId = utrNumber.trim() || upiData?.session_id || `utr_${Date.now()}`;
        const verified = await verifyPayment({
          plan_tier: checkoutPlan.id,
          billing_cycle: billingCycle,
          currency: currency,
          gateway: 'UPI' as any,
          transaction_id: txnId,
          amount: upiData?.amount || checkoutPlan.priceINR,
          user_id: 1
        });
        setCheckoutSuccess(`🎉 ${verified.message} Valid until ${verified.valid_until}.`);
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1800);
        return;
      }

      const session = await createCheckoutSession({
        plan_tier: checkoutPlan.id,
        billing_cycle: billingCycle,
        currency: currency,
        gateway: 'RAZORPAY',
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
        gateway: 'RAZORPAY',
        transaction_id: session.session_id || `tx_${Date.now()}`,
        amount: session.amount,
        user_id: 1
      });

      setCheckoutSuccess(`🎉 ${verified.message} Valid until ${verified.valid_until}.`);
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1800);
    } catch (err: any) {
      alert('Payment processing error: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const plans = [
    {
      id: 'STARTER',
      name: 'Starter Creator',
      priceINR: billingCycle === 'MONTHLY' ? 999 : 8999,
      priceUSD: billingCycle === 'MONTHLY' ? 12 : 119,
      credits: '300 Credits / mo',
      shorts: '30 AI Shorts',
      channels: '1 YouTube Channel',
      popular: false,
      badge: 'Popular for Beginners',
      features: [
        '1 Connected YouTube Channel',
        '30 Autonomous Shorts / Month',
        '3D Pixar High-Res Visuals',
        'Devanagari Hindi Voice Engine',
        'Script Quality QA Gate (>=85)',
        'Daily 10:00 AM Automated Upload'
      ]
    },
    {
      id: 'PRO',
      name: 'Pro Animator',
      priceINR: billingCycle === 'MONTHLY' ? 2499 : 22999,
      priceUSD: billingCycle === 'MONTHLY' ? 30 : 279,
      credits: '1,000 Credits / mo',
      shorts: '100 AI Shorts + Moving AI Clips',
      channels: 'Up to 3 YouTube Channels',
      popular: true,
      badge: '🔥 Best Value for Scaling',
      features: [
        'Up to 3 YouTube Channels',
        '100 Shorts or 22 Full Moving AI Videos',
        'Character Motion & Temporal Animation',
        'Character Universe Consistency (Chintu)',
        'Multi-Voice Emotion Acting',
        'Priority GPU Queue & 4K Visuals'
      ]
    },
    {
      id: 'AGENCY',
      name: 'Agency Empire',
      priceINR: billingCycle === 'MONTHLY' ? 5999 : 54999,
      priceUSD: billingCycle === 'MONTHLY' ? 72 : 659,
      credits: '3,000 Credits / mo',
      shorts: '300 Shorts or 65 Full Moving AI Videos',
      channels: 'Up to 10 YouTube Channels',
      popular: false,
      badge: 'For Channel Empire Owners',
      features: [
        'Up to 10 YouTube Channels',
        'Daily Multi-Post Automation (Morning & Evening)',
        'Full Moving AI Animation Engine (Kling/Luma)',
        'Multi-Project API Key Auto-Rotation',
        'Custom Character & Voice Tuning',
        '24/7 Priority Support & SLA'
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white font-sans pb-24">
      {/* Header Navigation */}
      <header className="border-b border-slate-800/80 bg-[#0F172A]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center font-bold text-white shadow-lg shadow-red-600/30">
              AT
            </div>
            <span className="text-xl font-black text-white tracking-tight">
              AutoTube AI
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <div className="text-xs bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-full text-slate-300">
              Active Tier: <span className="font-extrabold text-red-400">{currentPlan}</span> | Credits: <span className="font-extrabold text-emerald-400">{creditsBalance}</span>
            </div>
            <Link
              href="/dashboard"
              className="text-xs px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold transition"
            >
              Back to Dashboard →
            </Link>
          </div>
        </div>
      </header>

      {/* Main Section */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-extrabold uppercase tracking-wider">
            ⚡ Instant Dynamic UPI (0% Fee, GPay, PhonePe, Paytm, BHIM)
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight">
            Scale Your YouTube Empire with Autonomous AI
          </h1>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Select a plan to add credits, connect YouTube channels, and generate 3D moving AI story shorts automatically.
          </p>

          {/* Billing Controls */}
          <div className="pt-6 flex items-center justify-center gap-4">
            <div className="bg-slate-900 border border-slate-800 p-1 rounded-2xl flex items-center gap-1">
              <button
                onClick={() => setBillingCycle('MONTHLY')}
                className={`px-5 py-2 rounded-xl text-xs font-extrabold transition ${
                  billingCycle === 'MONTHLY'
                    ? 'bg-red-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Monthly Billing
              </button>
              <button
                onClick={() => setBillingCycle('ANNUAL')}
                className={`px-5 py-2 rounded-xl text-xs font-extrabold transition flex items-center gap-2 ${
                  billingCycle === 'ANNUAL'
                    ? 'bg-red-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Annual Billing
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">
                  Save 20%
                </span>
              </button>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-1 rounded-2xl flex items-center gap-1">
              <button
                onClick={() => setCurrency('INR')}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold ${
                  currency === 'INR' ? 'bg-slate-800 text-red-400 border border-slate-700' : 'text-slate-400'
                }`}
              >
                🇮🇳 ₹ INR
              </button>
              <button
                onClick={() => setCurrency('USD')}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold ${
                  currency === 'USD' ? 'bg-slate-800 text-red-400 border border-slate-700' : 'text-slate-400'
                }`}
              >
                🌐 $ USD
              </button>
            </div>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const price = currency === 'INR' ? plan.priceINR : plan.priceUSD;
            const symbol = currency === 'INR' ? '₹' : '$';
            const isCurrent = currentPlan === plan.id;

            return (
              <div
                key={plan.id}
                className={`rounded-3xl bg-[#0F172A]/90 border p-8 flex flex-col justify-between transition-all relative ${
                  plan.popular
                    ? 'border-red-500/80 shadow-2xl shadow-red-600/10 ring-1 ring-red-500/50'
                    : 'border-slate-800/80 hover:border-slate-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-red-600 text-white text-[11px] font-black tracking-wider uppercase shadow-lg shadow-red-600/30">
                    {plan.badge}
                  </div>
                )}

                <div>
                  <div className="text-xl font-extrabold text-white">{plan.name}</div>
                  <div className="text-xs text-red-400 font-bold mt-1">{plan.badge}</div>

                  <div className="mt-6 flex items-baseline gap-1">
                    <span className="text-4xl font-black text-white">
                      {symbol}{price.toLocaleString()}
                    </span>
                    <span className="text-slate-400 text-xs font-semibold">
                      /{billingCycle === 'MONTHLY' ? 'month' : 'year'}
                    </span>
                  </div>

                  <div className="mt-4 p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1">
                    <div className="text-xs font-extrabold text-emerald-400">⚡ {plan.credits}</div>
                    <div className="text-xs text-slate-300 font-medium">🎬 {plan.shorts}</div>
                    <div className="text-xs text-slate-400 font-medium">📺 {plan.channels}</div>
                  </div>

                  <ul className="mt-6 space-y-3 text-xs">
                    {plan.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-slate-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-8 pt-6 border-t border-slate-800/80">
                  <button
                    disabled={isCurrent}
                    onClick={() => handleOpenCheckout(plan)}
                    className={`w-full py-3.5 px-4 rounded-2xl font-extrabold transition text-xs flex items-center justify-center gap-2 ${
                      isCurrent
                        ? 'bg-slate-800 text-slate-500 cursor-default border border-slate-700'
                        : plan.popular
                        ? 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/25'
                        : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700'
                    }`}
                  >
                    {isCurrent ? (
                      <span>Current Active Plan</span>
                    ) : (
                      <span>Upgrade Plan ({symbol}{price.toLocaleString()}) →</span>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Security Trust Footer */}
        <div className="mt-16 text-center border-t border-slate-800/80 pt-10">
          <div className="text-slate-400 text-xs font-bold flex items-center justify-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" /> Instant Dynamic UPI & 256-Bit Encrypted Payments
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-slate-500 text-[11px] font-medium">
            <span>✓ Instant GPay / PhonePe / Paytm Intent</span>
            <span>✓ Dynamic QR Code Scanning</span>
            <span>✓ 0% Gateway Fee & Instant Credits</span>
            <span>✓ 24/7 Autonomous Channel Support</span>
          </div>
        </div>
      </main>

      {/* Multi-Gateway Checkout Modal */}
      {checkoutPlan && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-[#0F172A] border border-slate-800 rounded-3xl max-w-md w-full p-6 text-white shadow-2xl relative space-y-5">
            <button
              onClick={() => setCheckoutPlan(null)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-800"
            >
              <X className="w-4 h-4" />
            </button>

            <div>
              <span className="text-[10px] font-black uppercase tracking-widest text-red-400 bg-red-500/10 px-2.5 py-0.5 rounded-full border border-red-500/20">
                Checkout & Upgrade
              </span>
              <h3 className="text-xl font-extrabold mt-1">{checkoutPlan.name} Plan</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {currency === 'INR' ? `₹${checkoutPlan.priceINR}` : `$${checkoutPlan.priceUSD}`} / {billingCycle.toLowerCase()}
              </p>
            </div>

            {/* Instant UPI Header */}
            <div className="bg-slate-900 p-3 rounded-2xl border border-slate-800 text-center">
              <p className="text-xs font-bold text-emerald-400">⚡ Direct Instant UPI Payment (0% Fee)</p>
            </div>

            {/* Instant UPI Payment Body */}
            {selectedGateway === 'UPI' && (
              <div className="space-y-4">
                {upiData?.qr_code_url ? (
                  <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 text-center space-y-3">
                    <p className="text-xs font-bold text-slate-300">Scan QR Code with any UPI App</p>
                    <div className="bg-white p-2.5 rounded-2xl inline-block shadow-lg border-2 border-emerald-500/30">
                      <img
                        src={upiData.qr_code_url}
                        alt="UPI Payment QR Code"
                        className="w-44 h-44 object-contain"
                      />
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
                        {upiData.upi_id}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(upiData.upi_id);
                          setCopiedVpa(true);
                          setTimeout(() => setCopiedVpa(false), 2000);
                        }}
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-bold transition"
                      >
                        {copiedVpa ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 bg-slate-900 rounded-2xl text-center">
                    <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-xs text-slate-400 font-medium">Generating Dynamic UPI QR Code...</p>
                  </div>
                )}

                {/* Mobile Intent Buttons */}
                {upiData?.upi_link && (
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <a
                      href={upiData.upi_link}
                      className="py-2.5 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-300 hover:bg-blue-600/30 text-xs font-extrabold transition flex items-center justify-center gap-1"
                    >
                      <Smartphone className="w-3.5 h-3.5" /> GPay
                    </a>
                    <a
                      href={upiData.upi_link}
                      className="py-2.5 rounded-xl bg-purple-600/20 border border-purple-500/30 text-purple-300 hover:bg-purple-600/30 text-xs font-extrabold transition flex items-center justify-center gap-1"
                    >
                      <Smartphone className="w-3.5 h-3.5" /> PhonePe
                    </a>
                    <a
                      href={upiData.upi_link}
                      className="py-2.5 rounded-xl bg-sky-600/20 border border-sky-500/30 text-sky-300 hover:bg-sky-600/30 text-xs font-extrabold transition flex items-center justify-center gap-1"
                    >
                      <Smartphone className="w-3.5 h-3.5" /> Paytm
                    </a>
                  </div>
                )}

                {/* UTR Verification Input */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-300 flex items-center justify-between">
                    <span>12-Digit UTR / Transaction Ref No.</span>
                    <span className="text-[10px] text-slate-400 font-medium">From GPay/PhonePe App</span>
                  </label>
                  <input
                    type="text"
                    value={utrNumber}
                    onChange={(e) => setUtrNumber(e.target.value)}
                    placeholder="e.g. 425612349876"
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white font-mono font-bold placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                  />
                </div>
              </div>
            )}

            {/* Razorpay Option Body */}
            {selectedGateway === 'RAZORPAY' && (
              <div className="p-5 bg-slate-900 rounded-2xl border border-slate-800 space-y-3 text-center">
                <CreditCard className="w-8 h-8 text-blue-400 mx-auto" />
                <p className="text-xs font-bold text-slate-200">Razorpay Gateway Enabled</p>
                <p className="text-[11px] text-slate-400">
                  Pay via Netbanking, Credit/Debit Cards, or Wallet.
                </p>
              </div>
            )}

            {/* Success Feedback */}
            {checkoutSuccess && (
              <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold text-center">
                {checkoutSuccess}
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-2">
              <button
                type="button"
                disabled={isProcessing}
                onClick={handleExecutePayment}
                className="w-full py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 font-black text-xs text-white shadow-lg shadow-emerald-600/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Processing Payment...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" /> Submit & Activate Plan
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => setCheckoutPlan(null)}
                className="w-full py-2.5 text-xs text-slate-400 hover:text-white font-semibold transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
