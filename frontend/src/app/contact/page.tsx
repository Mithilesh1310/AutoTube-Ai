'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Mail, MessageSquare, Play, ArrowLeft, Send, CheckCircle2, MapPin, Clock, ShieldCheck } from 'lucide-react';

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

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
            <MessageSquare className="w-4 h-4" />
            <span>24/7 Creator Support</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight mb-2">
            Contact & Support
          </h1>
          <p className="text-sm text-neutral-500 mb-10">
            Have questions about YouTube automation, billing, or enterprise channel fleets? We're here to help.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Contact Form */}
            <div>
              {submitted ? (
                <div className="p-8 rounded-2xl bg-emerald-50 border border-emerald-100 text-center">
                  <div className="w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center mx-auto mb-3">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-bold text-emerald-900 mb-1">Message Received!</h3>
                  <p className="text-xs text-emerald-700 leading-relaxed">
                    Thank you for reaching out. Our support engineering team will reply to <strong>{email}</strong> within 24 business hours.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-neutral-700 mb-1 uppercase tracking-wider">
                      Your Name
                    </label>
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. John Doe"
                      className="w-full px-4 py-2.5 bg-neutral-50 border border-neutral-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-neutral-700 mb-1 uppercase tracking-wider">
                      Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@gmail.com"
                      className="w-full px-4 py-2.5 bg-neutral-50 border border-neutral-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-neutral-700 mb-1 uppercase tracking-wider">
                      Message / Inquiry
                    </label>
                    <textarea
                      required
                      rows={4}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Tell us how we can help your YouTube channel..."
                      className="w-full px-4 py-2.5 bg-neutral-50 border border-neutral-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 px-4 rounded-xl bg-neutral-900 hover:bg-neutral-800 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-neutral-900/10 transition"
                  >
                    <Send className="w-4 h-4" />
                    <span>Send Inquiry</span>
                  </button>
                </form>
              )}
            </div>

            {/* Direct Info & SLA Details */}
            <div className="space-y-6 md:pl-6 md:border-l border-neutral-100 flex flex-col justify-center">
              <div className="flex items-start gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-900">Direct Support Email</h4>
                  <p className="text-xs text-neutral-500 mt-0.5">support@autotube.ai</p>
                  <p className="text-xs text-neutral-500">billing@autotube.ai (Payment/Invoices)</p>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-900">Support Hours & SLA</h4>
                  <p className="text-xs text-neutral-500 mt-0.5">Monday to Saturday: 09:00 - 19:00 IST</p>
                  <p className="text-xs text-neutral-500">Average response time: &lt; 2 hours</p>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-neutral-900">Merchant Entity</h4>
                  <p className="text-xs text-neutral-500 mt-0.5">AutoTube AI Technologies</p>
                  <p className="text-xs text-neutral-500">Registered SaaS Provider</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
