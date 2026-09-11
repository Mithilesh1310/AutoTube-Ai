import Link from 'next/link';
import { RotateCcw, Play, ArrowLeft, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

export const metadata = {
  title: 'Refund & Cancellation Policy — AutoTube AI',
  description: 'AutoTube AI 14-day refund policy, credit usage rules, and subscription cancellation terms.',
};

export default function RefundPolicyPage() {
  return (
    <div className="min-h-screen bg-[#fafafc] text-neutral-800">
      <header className="h-16 border-b border-neutral-200/80 bg-white/80 backdrop-blur-md px-6 sm:px-12 flex items-center justify-between sticky top-0 z-30">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-neutral-900 flex items-center justify-center text-white">
            <Play className="w-4 h-4 fill-white" />
          </div>
          <span className="font-bold text-neutral-900 tracking-tight">AutoTube AI</span>
        </Link>
        <Link
          href="/"
          className="flex items-center gap-1.5 text-xs font-semibold text-neutral-600 hover:text-neutral-900 bg-neutral-100 hover:bg-neutral-200/80 px-3.5 py-1.5 rounded-xl transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Home</span>
        </Link>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12 sm:py-16">
        <div className="bg-white rounded-3xl border border-neutral-200/80 shadow-xl shadow-neutral-900/5 p-8 sm:p-12">
          <div className="flex items-center gap-2.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold w-fit mb-4">
            <RotateCcw className="w-4 h-4" />
            <span>Satisfaction Guarantee</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight mb-2">
            Refund & Cancellation Policy
          </h1>
          <p className="text-xs text-neutral-400 mb-8 font-medium">
            Last Updated: September 8, 2026 • Transparent & Creator-First Terms
          </p>

          <div className="prose prose-neutral max-w-none space-y-8 text-sm leading-relaxed text-neutral-600">
            <section className="p-6 rounded-2xl bg-indigo-50/50 border border-indigo-100">
              <h2 className="text-lg font-bold text-indigo-950 mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                1. 14-Day Money-Back Guarantee
              </h2>
              <p className="text-indigo-900/80">
                We want you to be completely satisfied with AutoTube AI. If you purchase any paid subscription plan and find that our platform does not suit your YouTube automation workflow, you can request a <strong>100% refund within 14 calendar days</strong> of your initial purchase date, subject to fair usage terms below.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                2. Fair Usage & GPU Rendering Cost Deductions
              </h2>
              <p className="mb-2">
                Because generating high-resolution 3D Disney Pixar animation frames, voiceovers, and FFmpeg video encoding consumes significant cloud GPU computing costs:
              </p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>
                  <strong>Full Refund:</strong> If you have consumed less than 20% of your plan's monthly credits within the first 14 days, you are eligible for a full 100% refund with zero hassle.
                </li>
                <li>
                  <strong>Pro-Rated Refund:</strong> If you have already rendered multiple videos and consumed more than 20% of credits, a fair pro-rated refund will be granted minus the actual computing GPU cost consumed.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                3. How to Cancel Your Subscription
              </h2>
              <p className="mb-3">
                You can cancel your recurring subscription at any time with zero penalty:
              </p>
              <ol className="list-decimal pl-5 space-y-1.5">
                <li>Log in to your AutoTube Studio Dashboard.</li>
                <li>Navigate to <strong>Studio Settings</strong> &rarr; <strong>Billing & Plans</strong>.</li>
                <li>Click <strong>Cancel Subscription</strong>.</li>
              </ol>
              <p className="mt-3 text-xs text-neutral-500">
                Your subscription will remain active until the end of your current paid billing period, and no further charges will be billed to your payment card.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                4. Refund Processing Timeline
              </h2>
              <div className="flex items-start gap-3 p-4 rounded-2xl bg-neutral-50 border border-neutral-200/80">
                <Clock className="w-5 h-5 text-neutral-500 shrink-0 mt-0.5" />
                <p className="text-xs text-neutral-600">
                  Approved refunds are automatically processed via Stripe or Razorpay back to your original payment method (Credit/Debit Card, UPI, Netbanking) within <strong>5 to 7 business days</strong> depending on your bank.
                </p>
              </div>
            </section>

            <section className="pt-4 border-t border-neutral-200">
              <h2 className="text-lg font-bold text-neutral-900 mb-2">
                5. Requesting a Refund
              </h2>
              <p>
                To request a refund, please send an email from your registered account email to:
              </p>
              <p className="font-semibold text-neutral-900 mt-2">
                Email: billing@autotube.ai <br />
                Subject: Refund Request - [Your Account Email] <br />
                Our billing support team responds within 24 business hours.
              </p>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
