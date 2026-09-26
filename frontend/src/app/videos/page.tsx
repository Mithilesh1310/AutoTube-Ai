'use client';

import { useEffect, useState } from 'react';
import { fetchVideos } from '@/lib/api';
import { VideoRecord } from '@/lib/types';
import { Film, Youtube, Download, Play, Search, X, Sparkles } from 'lucide-react';
import AuthGuard from '@/components/AuthGuard';

function getMediaUrl(path?: string, ytId?: string, isThumb = false): string {
  if (!path) {
    if (isThumb && ytId && !ytId.startsWith('yt_demo') && !ytId.startsWith('NO_UPLOAD') && !ytId.startsWith('LOCAL_TEST')) {
      return `https://i.ytimg.com/vi/${ytId}/hqdefault.jpg`;
    }
    return '';
  }
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const clean = path.replace(/\\/g, '/').replace(/^\.?\/?storage\//, '/storage/');
  return clean.startsWith('/') ? clean : `/${clean}`;
}

export default function VideosPage() {
  const [videos, setVideos] = useState<VideoRecord[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoRecord | null>(null);
  const [filterType, setFilterType] = useState<'ALL' | 'SHORT' | 'LONG'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchVideos();
        setVideos(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredVideos = videos.filter((v) => {
    const matchesType = filterType === 'ALL' || v.video_type === filterType;
    const matchesSearch = v.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <AuthGuard>
    <div className="space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Film className="w-6 h-6 text-purple-400" /> Generated Videos Gallery
          </h1>
          <p className="text-xs text-slate-400 mt-1">Browse all autonomous Hindi Shorts and Cartoon stories</p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          {/* Search Bar */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search Hindi titles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          {/* Type Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800/80 w-full sm:w-auto">
            {(['ALL', 'SHORT', 'LONG'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  filterType === t ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                {t === 'ALL' ? 'All' : t === 'SHORT' ? 'Shorts' : 'Stories'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Videos Grid */}
      {filteredVideos.length === 0 ? (
        <div className="p-16 text-center rounded-2xl glass-card space-y-3">
          <Film className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-200">No videos match your search</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Try adjusting your search terms or filter selection.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredVideos.map((v) => (
            <div
              key={v.id}
              className="group rounded-2xl glass-card overflow-hidden glass-card-hover flex flex-col justify-between"
            >
              <div>
                {/* Thumbnail Header */}
                <div
                  onClick={() => setSelectedVideo(v)}
                  className="relative aspect-video bg-black cursor-pointer overflow-hidden group"
                >
                  {getMediaUrl(v.thumbnail_path, v.youtube_video_id, true) ? (
                    <img
                      src={getMediaUrl(v.thumbnail_path, v.youtube_video_id, true)}
                      alt={v.title}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-slate-600 bg-slate-950">
                      <Film className="w-10 h-10 mb-2 opacity-50" />
                      <span className="text-[11px] font-medium">Rendered MP4 Preview</span>
                    </div>
                  )}

                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="w-12 h-12 rounded-full bg-purple-600/90 text-white flex items-center justify-center shadow-xl">
                      <Play className="w-5 h-5 fill-current ml-0.5" />
                    </div>
                  </div>

                  <span
                    className={`absolute top-3 left-3 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider shadow-md ${
                      v.video_type === 'SHORT' ? 'bg-purple-600 text-white' : 'bg-blue-600 text-white'
                    }`}
                  >
                    {v.video_type}
                  </span>
                </div>

                {/* Details */}
                <div className="p-5 space-y-3">
                  <h3 className="font-bold text-sm text-white line-clamp-2 leading-snug group-hover:text-purple-300 transition-colors">
                    {v.title}
                  </h3>
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                    <span>Status: <strong className="text-emerald-400 font-semibold">{v.status}</strong></span>
                    <span>Mode: <strong className="text-amber-400 font-semibold">{v.publish_mode}</strong></span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-5 pt-0 flex items-center gap-2">
                <button
                  onClick={() => setSelectedVideo(v)}
                  className="flex-1 py-2.5 rounded-xl bg-purple-600/15 text-purple-300 border border-purple-500/30 text-xs font-bold hover:bg-purple-600/25 transition-all flex items-center justify-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5 fill-current" /> Preview Player
                </button>

                {v.youtube_url && (
                  <a
                    href={v.youtube_url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2.5 rounded-xl bg-red-600/15 text-red-400 border border-red-500/30 hover:bg-red-600/25 transition-all"
                    title="Watch on YouTube"
                  >
                    <Youtube className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Video Modal Player */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-3xl w-full p-4 sm:p-6 space-y-4 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                  selectedVideo.video_type === 'SHORT' ? 'bg-purple-600 text-white' : 'bg-blue-600 text-white'
                }`}>
                  {selectedVideo.video_type}
                </span>
                <h3 className="font-bold text-lg text-white mt-1 line-clamp-1">{selectedVideo.title}</h3>
              </div>
              <button
                onClick={() => setSelectedVideo(null)}
                className="w-8 h-8 rounded-full bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800">
              <video
                src={getMediaUrl(selectedVideo.video_path)}
                controls
                autoPlay
                className="w-full h-full object-contain"
              />
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2">
              <div className="text-xs text-slate-400">
                Created: <span className="text-slate-200 font-medium">{selectedVideo.created_at}</span>
              </div>
              <div className="flex items-center gap-3">
                {selectedVideo.video_path && (
                  <a
                    href={getMediaUrl(selectedVideo.video_path)}
                    download
                    className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-purple-600/25 transition-all"
                  >
                    <Download className="w-3.5 h-3.5" /> Download MP4 File
                  </a>
                )}
                {selectedVideo.youtube_url && (
                  <a
                    href={selectedVideo.youtube_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2 rounded-xl bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 text-xs font-bold flex items-center gap-1.5 transition-all"
                  >
                    <Youtube className="w-3.5 h-3.5" /> Watch on YouTube
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
    </AuthGuard>
  );
}

