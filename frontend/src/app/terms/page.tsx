import Link from 'next/link';
import { FileText, Play, ArrowLeft, CheckCircle2, ShieldAlert } from 'lucide-react';

export const metadata = {
  title: 'Terms of Service — AutoTube AI',
  description: 'AutoTube AI Terms of Service, Commercial Usage Rights, and Platform Agreement.',
};

export default function TermsOfServicePage() {
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
            <FileText className="w-4 h-4" />
            <span>Legal Agreement</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight mb-2">
            Terms of Service
          </h1>
          <p className="text-xs text-neutral-400 mb-8 font-medium">
            Last Updated: September 8, 2026 • Effective Immediately
          </p>

          <div className="prose prose-neutral max-w-none space-y-8 text-sm leading-relaxed text-neutral-600">
            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                1. Acceptance of Terms
              </h2>
              <p>
                By creating an account, accessing, or using AutoTube AI ("Platform", "we", "us"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.
              </p>
            </section>

            <section className="p-6 rounded-2xl bg-emerald-50/50 border border-emerald-100">
              <h2 className="text-lg font-bold text-emerald-950 mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                2. 100% Commercial Rights & Video Ownership
              </h2>
              <p className="text-emerald-900/80 mb-2">
                <strong>You own what you generate.</strong> When you create videos, animated stories, Shorts, sound effects, and custom thumbnails using AutoTube AI:
              </p>
              <ul className="list-disc pl-5 space-y-1.5 text-emerald-900/80">
                <li>You receive full, royalty-free, worldwide commercial rights to upload, publish, monetize, distribute, and broadcast the rendered media anywhere.</li>
                <li>You retain 100% of all ad revenue, sponsorship income, and YouTube Partner Program monetization earned from your videos.</li>
                <li>AutoTube AI claims no royalties or ownership over your finalized video content.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                3. YouTube Terms of Service Compliance
              </h2>
              <p>
                AutoTube AI connects to YouTube via official Google YouTube Data API services. By connecting your YouTube channel to AutoTube AI, you also agree to be bound by the{' '}
                <a
                  href="https://www.youtube.com/t/terms"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-600 underline font-semibold"
                >
                  YouTube Terms of Service
                </a>{' '}
                and the{' '}
                <a
                  href="https://policies.google.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-600 underline font-semibold"
                >
                  Google Privacy Policy
                </a>.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                4. Acceptable Use Policy
              </h2>
              <p className="mb-2">You agree not to use the Platform to generate or publish:</p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>Content that is illegal, defamatory, harassing, hateful, or promotes violence.</li>
                <li>Explicit, adult, or child-harmful material.</li>
                <li>Malicious deepfakes designed to defraud, mislead, or impersonate real living individuals without consent.</li>
                <li>Content intended to bypass or spam YouTube's Community Guidelines.</li>
              </ul>
              <p className="mt-2 text-xs text-neutral-400">
                Accounts violating these safety standards will be terminated immediately without refund.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                5. Subscription Billing, Credits & Renewals
              </h2>
              <p className="mb-2">
                AutoTube AI offers monthly and annual subscription tiers (Starter, Pro, Agency) and pay-as-you-go credit packs:
              </p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>Subscriptions automatically renew at the end of each billing cycle unless cancelled prior to the renewal date via the settings dashboard.</li>
                <li>AI video generation consumes credits based on video length and rendering mode (e.g. Image Motion vs Full Animation).</li>
                <li>Unused monthly credits roll over as long as the subscription remains continuously active.</li>
              </ul>
            </section>

            <section className="pt-4 border-t border-neutral-200">
              <h2 className="text-lg font-bold text-neutral-900 mb-2">
                6. Limitation of Liability
              </h2>
              <p>
                AutoTube AI is provided on an "as is" and "as available" basis. We are not liable for YouTube algorithm fluctuations, video view counts, subscriber growth rates, or channel penalties incurred through YouTube guideline violations.
              </p>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
