'use client';

import { useEffect, useState } from 'react';
import { fetchCharacters } from '@/lib/api';
import { CharacterItem } from '@/lib/types';
import { Users, Sparkles, Volume2, Palette, Smile, ShieldCheck } from 'lucide-react';

export default function CharactersPage() {
  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchCharacters();
        setCharacters(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-blue-400" /> Cartoon Universe Character Bible
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Persistent character memory automatically injected into AI visual scene generators & Hindi TTS voice engines.
        </p>
      </div>

      {/* Characters Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {characters.map((c) => (
          <div key={c.character_id} className="p-6 rounded-3xl glass-card glass-card-hover space-y-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div>
                  <span className="text-[10px] font-bold font-mono text-blue-400 uppercase tracking-widest block mb-0.5">
                    #{c.character_id}
                  </span>
                  <h3 className="text-lg font-extrabold text-white flex items-center gap-2">
                    {c.name} <span className="text-xs font-medium text-slate-400">({c.species})</span>
                  </h3>
                </div>
                <div className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-extrabold shadow-inner">
                  3D Pixar Style
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-start gap-2">
                  <Smile className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-slate-400 font-semibold block text-[11px]">Personality Traits</span>
                    <p className="text-slate-200 mt-0.5 font-medium leading-relaxed">{c.personality}</p>
                  </div>
                </div>

                <div className="flex items-start gap-2">
                  <Palette className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-slate-400 font-semibold block text-[11px]">Color Palette & Outfit</span>
                    <p className="text-slate-200 mt-0.5 font-medium">{c.color_palette}</p>
                    <p className="text-slate-400 text-[11px] mt-0.5">{c.clothing || 'Standard 3D signature attire'}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-1.5">
                <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xs">
                  <Sparkles className="w-3.5 h-3.5" /> Visual Prompt Memory
                </div>
                <p className="text-slate-300 font-mono text-[11px] leading-relaxed italic">{c.visual_prompt_base}</p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <Volume2 className="w-4 h-4 text-emerald-400" />
                  <span>Voice: <strong className="text-white font-semibold">{c.voice_config?.voice_id}</strong></span>
                </div>
                <span className="text-emerald-400 font-mono text-[11px] font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  {c.voice_config?.pitch} pitch
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

