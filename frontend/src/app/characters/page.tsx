'use client';

import { useEffect, useState } from 'react';
import { fetchCharacters, createCharacter } from '@/lib/api';
import { CharacterItem } from '@/lib/types';
import AuthGuard from '@/components/AuthGuard';
import { Users, Sparkles, Volume2, Palette, Smile, Plus, X, UserPlus } from 'lucide-react';

export default function CharactersPage() {
  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [species, setSpecies] = useState('Cartoon Boy');
  const [personality, setPersonality] = useState('Brave, cheerful and adventurous');
  const [physicalDesc, setPhysicalDesc] = useState('Adorable 3D Pixar cartoon style with big expressive eyes and friendly smile');
  const [clothing, setClothing] = useState('Vibrant red hoodie and denim jeans');
  const [colorPalette, setColorPalette] = useState('Red, Blue, Warm Gold');
  const [voiceId, setVoiceId] = useState('hi-IN-SwaraNeural');

  const loadCharacters = async () => {
    try {
      setLoading(true);
      const data = await fetchCharacters();
      setCharacters(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCharacters();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Please enter a character name');
      return;
    }
    try {
      setSubmitting(true);
      await createCharacter({
        name: name.trim(),
        species: species.trim(),
        personality: personality.trim(),
        physical_description: physicalDesc.trim(),
        clothing: clothing.trim(),
        color_palette: colorPalette.trim(),
        voice_id: voiceId
      });
      setShowModal(false);
      setName('');
      await loadCharacters();
    } catch (err: any) {
      alert(err.message || 'Failed to create custom character');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthGuard>
      <div className="space-y-8 animate-in fade-in duration-300 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
              <Users className="w-6 h-6 text-blue-400" /> Cartoon Universe Character Bible
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Persistent custom character memory automatically injected into AI visual generators & Hindi TTS voice engines.
            </p>
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-xs shadow-lg shadow-blue-600/30 transition shrink-0"
          >
            <Plus className="w-4 h-4" /> Create Custom Character
          </button>
        </div>

        {/* Characters Cards Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 rounded-3xl bg-slate-900/50 border border-slate-800 animate-pulse"></div>
            ))}
          </div>
        ) : (
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
        )}

        {/* Create Character Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-3xl bg-slate-900 border border-slate-800 p-6 shadow-2xl relative">
              <button
                onClick={() => setShowModal(false)}
                className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>

              <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-blue-400" /> Create Custom 3D Character
              </h2>
              <p className="text-xs text-slate-400 mb-5">
                Define your own unique signature 3D Pixar character. AI will use this exact memory in every video scene!
              </p>

              <form onSubmit={handleCreate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Character Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Birbal / Chinki / Raju"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Species / Role</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Cartoon Boy / Cute Lion / Fairy"
                      value={species}
                      onChange={(e) => setSpecies(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Personality & Character Traits</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Clever, witty, highly intelligent and humorous"
                    value={personality}
                    onChange={(e) => setPersonality(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Physical 3D Appearance Details</label>
                  <textarea
                    required
                    rows={2}
                    placeholder="e.g. Adorable 3D Pixar render, big brown expressive eyes, cheerful face"
                    value={physicalDesc}
                    onChange={(e) => setPhysicalDesc(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Clothing & Outfit</label>
                    <input
                      type="text"
                      placeholder="e.g. Royal traditional turban & silk kurta"
                      value={clothing}
                      onChange={(e) => setClothing(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Color Palette</label>
                    <input
                      type="text"
                      placeholder="e.g. Gold, Royal Blue, Emerald"
                      value={colorPalette}
                      onChange={(e) => setColorPalette(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Hindi Voice Engine</label>
                  <select
                    value={voiceId}
                    onChange={(e) => setVoiceId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="hi-IN-SwaraNeural">hi-IN-SwaraNeural (Female Expressive Hindi Voice)</option>
                    <option value="hi-IN-MadhurNeural">hi-IN-MadhurNeural (Male Storyteller Hindi Voice)</option>
                  </select>
                </div>

                <div className="pt-3 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-xs shadow-lg shadow-blue-600/30 transition disabled:opacity-50"
                  >
                    {submitting ? 'Creating...' : 'Save Character'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
