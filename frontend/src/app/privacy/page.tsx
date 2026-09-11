import Link from 'next/link';
import { ShieldCheck, Play, ArrowLeft, Lock, Database, EyeOff, Globe } from 'lucide-react';

export const metadata = {
  title: 'Privacy Policy — AutoTube AI',
  description: 'AutoTube AI Privacy Policy and Google API Services User Data Disclosure.',
};

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-[#fafafc] text-neutral-800">
      {/* Top Navigation */}
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
          {/* Header */}
          <div className="flex items-center gap-2.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold w-fit mb-4">
            <ShieldCheck className="w-4 h-4" />
            <span>Compliance & Data Protection</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight mb-2">
            Privacy Policy
          </h1>
          <p className="text-xs text-neutral-400 mb-8 font-medium">
            Last Updated: September 8, 2026 • Effective Date: September 8, 2026
          </p>

          <div className="prose prose-neutral max-w-none space-y-8 text-sm leading-relaxed text-neutral-600">
            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3 flex items-center gap-2">
                1. Overview & Commitment
              </h2>
              <p>
                AutoTube AI ("we", "our", or "the Platform") provides an autonomous AI YouTube channel production, automation, and video scaling software-as-a-service. We take your privacy and data security seriously. This Privacy Policy details the types of information we collect, how it is used, secured, and your rights regarding your personal and YouTube channel data.
              </p>
            </section>

            <section className="p-6 rounded-2xl bg-indigo-50/50 border border-indigo-100">
              <h2 className="text-lg font-bold text-indigo-950 mb-3 flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-600" />
                2. Google API Services & YouTube User Data Disclosure
              </h2>
              <p className="text-indigo-900/80 mb-3">
                AutoTube AI uses Google APIs (specifically the <strong>YouTube Data API v3</strong>) to allow creators to connect their YouTube channels and autonomously publish generated videos, custom thumbnails, and descriptions directly to YouTube on their scheduled time.
              </p>
              <ul className="list-disc pl-5 space-y-2 text-indigo-900/80">
                <li>
                  <strong>Scope of Access:</strong> We only request the <code>youtube.upload</code> and <code>youtube.readonly</code> permissions necessary to upload approved video content and display view/subscriber counts on your creator dashboard.
                </li>
                <li>
                  <strong>No Selling or Sharing:</strong> AutoTube AI never sells, rents, or shares your Google or YouTube account data with third parties.
                </li>
                <li>
                  <strong>Encryption at Rest:</strong> All YouTube OAuth Refresh Tokens and Client Credentials are encrypted using industry-standard <strong>AES-256 (Fernet)</strong> encryption in our database. Plaintext tokens are never stored or exposed in logs.
                </li>
                <li>
                  <strong>Revocation:</strong> You can disconnect your YouTube channel at any moment from your AutoTube Studio Settings or directly via the{' '}
                  <a
                    href="https://myaccount.google.com/permissions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline font-semibold text-indigo-700"
                  >
                    Google Security Settings Permissions Page
                  </a>. Upon disconnection, your stored tokens are permanently deleted from our database.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                3. Information We Collect
              </h2>
              <div className="space-y-3">
                <p>
                  <strong>Account Information:</strong> When you register, we collect your name, email address, password hash, and assigned user ID to manage authentication, subscription tiers, and credit balances.
                </p>
                <p>
                  <strong>Generated Content & Prompts:</strong> Video titles, Devanagari Hindi scripts, 3D visual generation prompts, voiceover audio files, and rendered MP4 files generated through your pipelines are stored in isolated storage associated with your user ID.
                </p>
                <p>
                  <strong>Billing & Payment Information:</strong> Payment transactions are handled directly through secure, PCI-DSS certified payment gateways (Stripe and Razorpay). We never collect or store your full credit card number or bank account passwords on our servers.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                4. Third-Party AI Engine Disclosures
              </h2>
              <p>
                To generate high-fidelity scripts, images, audio, and videos, AutoTube AI communicates with AI cloud APIs including Google Gemini, Pollinations / Flux AI, and Microsoft EdgeTTS. Prompts sent to these APIs are strictly used to render your requested scene assets and are not used to train proprietary public models.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-bold text-neutral-900 mb-3">
                5. Data Retention & Account Deletion
              </h2>
              <p>
                We retain user data as long as your account remains active. You can request complete deletion of your account, generated video files, and channel access at any time by contacting us at <strong>privacy@autotube.ai</strong> or through your account dashboard.
              </p>
            </section>

            <section className="pt-4 border-t border-neutral-200">
              <h2 className="text-lg font-bold text-neutral-900 mb-2">
                6. Contact Information
              </h2>
              <p>
                For questions, concerns, or data requests regarding this Privacy Policy, please contact our Data Protection Officer at:
              </p>
              <p className="font-semibold text-neutral-900 mt-2">
                Email: support@autotube.ai <br />
                Entity: AutoTube AI Autonomous Systems Private Limited
              </p>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
