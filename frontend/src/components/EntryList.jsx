import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
// ReactPlayer removed - using native iframe for reliability
import remarkGfm from 'remark-gfm';
import { getEntries } from '../utils/api';
import { formatToIST } from '../utils/dateUtils';

// Helper to ensure URLs are clickable in Markdown (handled by remark-gfm mostly, but fallback)
const linkify = (text) => text; // Disabled manual linkify as remark-gfm handles it better

// Helper: Extract YouTube video ID from any YouTube URL format
const getYouTubeVideoId = (url) => {
    if (!url) return null;
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    return null;
};

// Helper: Get the video URL for an entry (checks metadata first, then content)
const getVideoUrl = (entry) => {
    // Priority 1: Explicit source_url from backend metadata
    const metaUrl = entry.entry_metadata?.source_url;
    if (metaUrl) return metaUrl;

    // Priority 2: Extract from content text
    const text = entry.processed_content || entry.raw_content || '';
    const urlMatch = text.match(/(https?:\/\/[^\s\)]+(?:youtube\.com|youtu\.be)[^\s\)]*)/i);
    if (urlMatch) return urlMatch[0];

    // Priority 3: Any URL in content (for non-YouTube links)
    const anyUrl = text.match(/(https?:\/\/[^\s\)]+)/);
    return anyUrl ? anyUrl[0] : null;
};

// Helper: Get the display title for an entry
const getEntryTitle = (entry) => {
    // Priority 1: title stored in metadata by AI
    if (entry.entry_metadata?.title) return entry.entry_metadata.title;
    // Priority 2: first meaningful line of processed content (strip markdown/urls)
    const text = (entry.processed_content || entry.raw_content || '').trim();
    const firstLine = text.split('\n')[0].replace(/[#*_~`>]/g, '').replace(/https?:\/\/\S+/g, '').trim();
    if (firstLine && firstLine.length > 3) return firstLine.substring(0, 80);
    return null;
};

// Helper: Strip URLs from text for collapsed preview (show only metadata, no raw URLs)
const stripUrls = (text) => {
    if (!text) return '';
    return text
        .replace(/https?:\/\/\S+/g, '')  // Remove URLs
        .replace(/URL:\s*/gi, '')          // Remove "URL:" labels left behind
        .replace(/\n{3,}/g, '\n\n')        // Collapse excess newlines
        .trim();
};

// Custom link renderer for ReactMarkdown — opens all links in new tab
const MarkdownLink = ({ href, children }) => (
    <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 underline hover:text-blue-800"
        onClick={(e) => e.stopPropagation()}
    >
        {children}
    </a>
);

// Helper: Build URL for media files served by backend
// Handles both old paths (backend/static/uploads/...) and new paths (static/uploads/...)
const getMediaUrl = (filePath) => {
    if (!filePath) return null;
    // Old format: backend/static/uploads/... → /api/uploads/...
    if (filePath.startsWith('backend/static/')) {
        return filePath.replace('backend/static', '/api');
    }
    // New format: static/uploads/... → /api/uploads/...
    if (filePath.startsWith('static/')) {
        return filePath.replace('static', '/api');
    }
    return filePath;
};

// Type icons mapping
const typeIcons = {
    text: '📝',
    image: '🖼️',
    audio: '🎤',
    video: '🎥',
    link: '🔗',
    youtube: '🎬'
};

function EntryList() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedEntryId, setExpandedEntryId] = useState(null);
    const [lightboxImage, setLightboxImage] = useState(null);

    // Get filter from URL params
    const typeFilter = searchParams.get('type') || '';

    useEffect(() => {
        fetchEntries();
    }, [typeFilter]);

    const fetchEntries = async () => {
        try {
            setLoading(true);
            const params = { limit: 100 };
            if (typeFilter) {
                params.content_type = typeFilter;
            }
            const res = await getEntries(params);
            setEntries(res.data.entries);
        } catch (error) {
            console.error('Error fetching entries:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTypeFilter = (type) => {
        if (type) {
            setSearchParams({ type });
        } else {
            setSearchParams({});
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6 fade-in">
            <div className="retro-card">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-4">
                        <Link to="/" className="text-retro-accent hover:underline">← Dashboard</Link>
                        <h2 className="text-2xl font-bold">
                            {typeFilter ? `${typeFilter.charAt(0).toUpperCase() + typeFilter.slice(1)} Entries` : 'All Entries'}
                            {typeFilter && typeIcons[typeFilter]}
                        </h2>
                    </div>
                    <span className="text-gray-500">{entries.length} entries</span>
                </div>

                {/* Type Filter Tabs */}
                <div className="flex flex-wrap gap-2 mb-6">
                    <button
                        onClick={() => handleTypeFilter('')}
                        className={`px-4 py-2 rounded-lg border-2 border-black transition-all ${!typeFilter ? 'bg-retro-accent text-white' : 'bg-gray-100 hover:bg-gray-200'
                            }`}
                    >
                        All
                    </button>
                    {Object.entries(typeIcons).map(([type, icon]) => (
                        <button
                            key={type}
                            onClick={() => handleTypeFilter(type)}
                            className={`px-4 py-2 rounded-lg border-2 border-black transition-all ${typeFilter === type ? 'bg-retro-accent text-white' : 'bg-gray-100 hover:bg-gray-200'
                                }`}
                        >
                            {icon} {type.charAt(0).toUpperCase() + type.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Entries List */}
                {entries.length === 0 ? (
                    <p className="text-gray-500 text-center py-12">
                        No {typeFilter || ''} entries found.
                    </p>
                ) : (
                    <div className="space-y-3">
                        {entries.map((entry) => (
                            <div
                                key={entry.id}
                                className="p-4 bg-gray-50 rounded-lg border-2 border-gray-200 hover:border-retro-accent transition-all cursor-pointer"
                                onClick={() => setExpandedEntryId(expandedEntryId === entry.id ? null : entry.id)}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 w-full"> {/* Ensure width for player */}
                                        {/* Bold Title */}
                                        {getEntryTitle(entry) && (
                                            <h3 className="text-base font-bold text-gray-900 mb-1 leading-snug">
                                                {typeIcons[entry.content_type] || '📄'} {getEntryTitle(entry)}
                                            </h3>
                                        )}
                                        {/* Metadata row */}
                                        <div className="flex items-center flex-wrap gap-2 mb-2 text-sm">
                                            {!getEntryTitle(entry) && (
                                                <span className="text-lg">
                                                    {typeIcons[entry.content_type] || '📄'}
                                                </span>
                                            )}
                                            {entry.category && (
                                                <span className="retro-badge bg-blue-100 text-blue-800">
                                                    {entry.category.name}
                                                    {entry.subcategory && <span className="text-gray-500 text-xs ml-1">/ {entry.subcategory.name}</span>}
                                                </span>
                                            )}
                                            {entry.content_type === 'audio' && (
                                                <span className="text-xs text-gray-500 italic">(Voice Note)</span>
                                            )}
                                            {entry.entry_metadata?.is_content_idea && (
                                                <span className="retro-badge bg-yellow-100 text-yellow-800 text-xs">💡 Idea</span>
                                            )}
                                        </div>

                                        {expandedEntryId === entry.id ? (
                                            <div className="mt-2 fade-in">
                                                <div className="bg-white p-3 rounded border border-gray-300 mb-2">
                                                    <p className="text-sm font-bold text-gray-700 mb-1">Full Content:</p>
                                                    <div className="text-sm text-gray-800 prose prose-sm max-w-none">
                                                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: MarkdownLink }}>
                                                            {entry.processed_content || entry.raw_content}
                                                        </ReactMarkdown>
                                                    </div>
                                                </div>

                                                {/* Media Rendering */}
                                                <div className="mt-3 space-y-3">
                                                    {/* Local File Rendering */}
                                                    {entry.file_path && (
                                                        <div>
                                                            {entry.content_type === 'image' && (
                                                                <div>
                                                                    <p className="text-xs font-semibold text-gray-500 mb-1">📎 Entry Attachment:</p>
                                                                    <img
                                                                        src={getMediaUrl(entry.file_path)}
                                                                        alt="Entry attachment"
                                                                        className="max-w-full h-auto rounded-lg shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
                                                                        style={{ maxWidth: '480px' }}
                                                                        onClick={(e) => { e.stopPropagation(); setLightboxImage(getMediaUrl(entry.file_path)); }}
                                                                    />
                                                                    <p className="text-xs text-gray-400 mt-1">Click image to enlarge</p>
                                                                </div>
                                                            )}
                                                            {entry.content_type === 'video' && (
                                                                <video
                                                                    controls
                                                                    src={getMediaUrl(entry.file_path)}
                                                                    className="max-w-full rounded-lg shadow-sm"
                                                                />
                                                            )}
                                                            {entry.content_type === 'audio' && (
                                                                <audio
                                                                    controls
                                                                    src={getMediaUrl(entry.file_path)}
                                                                    className="w-full"
                                                                />
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* YouTube Embed (native iframe - bulletproof) */}
                                                    {(() => {
                                                        const videoUrl = getVideoUrl(entry);
                                                        const videoId = getYouTubeVideoId(videoUrl);
                                                        if (videoId) {
                                                            return (
                                                                <div style={{ maxWidth: '480px' }}>
                                                                    <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                                                                        <iframe
                                                                            src={`https://www.youtube.com/embed/${videoId}`}
                                                                            title="YouTube video"
                                                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                                            allowFullScreen
                                                                            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            );
                                                        } else if (videoUrl && (entry.content_type === 'youtube' || entry.content_type === 'link')) {
                                                            return (
                                                                <a
                                                                    href={videoUrl}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-blue-600 underline text-sm"
                                                                    onClick={(e) => e.stopPropagation()}
                                                                >
                                                                    🔗 Open Link
                                                                </a>
                                                            );
                                                        }
                                                        return null;
                                                    })()}
                                                </div>
                                            </div>
                                        ) : (
                                            <div>
                                                {/* Collapsed view: show video embed for YouTube entries */}
                                                {(() => {
                                                    const videoUrl = getVideoUrl(entry);
                                                    const videoId = getYouTubeVideoId(videoUrl);
                                                    if (videoId) {
                                                        return (
                                                            <div style={{ maxWidth: '480px', marginBottom: '8px' }}>
                                                                <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                                                                    <iframe
                                                                        src={`https://www.youtube.com/embed/${videoId}`}
                                                                        title="YouTube video"
                                                                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                                        allowFullScreen
                                                                        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                                                                    />
                                                                </div>
                                                            </div>
                                                        );
                                                    }
                                                    return null;
                                                })()}
                                                {/* Collapsed view: show image thumbnail for image entries */}
                                                {entry.content_type === 'image' && entry.file_path && (
                                                    <div style={{ marginBottom: '8px' }}>
                                                        <img
                                                            src={getMediaUrl(entry.file_path)}
                                                            alt="Entry thumbnail"
                                                            className="rounded-lg shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
                                                            style={{ maxWidth: '200px', maxHeight: '150px', objectFit: 'cover' }}
                                                            onClick={(e) => { e.stopPropagation(); setLightboxImage(getMediaUrl(entry.file_path)); }}
                                                        />
                                                    </div>
                                                )}
                                                <div className="text-sm text-gray-700 line-clamp-2">
                                                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: MarkdownLink }}>
                                                        {stripUrls(entry.processed_content || entry.raw_content)}
                                                    </ReactMarkdown>
                                                </div>
                                            </div>
                                        )}

                                        <p className="text-xs text-gray-500 mt-2">
                                            {formatToIST(entry.created_at)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Lightbox Overlay */}
            {lightboxImage && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(0, 0, 0, 0.85)' }}
                    onClick={() => setLightboxImage(null)}
                    onKeyDown={(e) => { if (e.key === 'Escape') setLightboxImage(null); }}
                    tabIndex={0}
                    ref={(el) => el && el.focus()}
                >
                    <button
                        onClick={() => setLightboxImage(null)}
                        className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors z-50"
                        style={{ fontSize: '2rem', lineHeight: 1, background: 'none', border: 'none', cursor: 'pointer' }}
                        aria-label="Close lightbox"
                    >
                        ✕
                    </button>
                    <p className="absolute bottom-4 text-gray-400 text-sm">Click anywhere or press ESC to close</p>
                    <img
                        src={lightboxImage}
                        alt="Full size view"
                        className="rounded-lg shadow-2xl"
                        style={{ maxWidth: '90vw', maxHeight: '90vh', objectFit: 'contain' }}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            )}
        </div>
    );
}

export default EntryList;

