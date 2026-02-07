import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getEntries } from '../utils/api';
import { formatToIST } from '../utils/dateUtils';

// Helper to strip HTML tags
const stripHtml = (html) => {
    if (!html) return '';
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
};

// Type icons mapping
const typeIcons = {
    text: '📝',
    image: '🖼️',
    audio: '🎤',
    video: '🎥',
    link: '🔗'
};

function EntryList() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedEntryId, setExpandedEntryId] = useState(null);

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
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <span className="text-lg">
                                                {typeIcons[entry.content_type] || '📄'}
                                            </span>
                                            {entry.category && (
                                                <span className="retro-badge bg-blue-100 text-blue-800">
                                                    {entry.category.name}
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
                                                    <p className="text-sm text-gray-800 whitespace-pre-wrap">
                                                        {stripHtml(entry.processed_content || entry.raw_content)}
                                                    </p>
                                                </div>
                                                {entry.file_path && (
                                                    <p className="text-xs text-gray-500">📁 File: {entry.file_path}</p>
                                                )}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-gray-700 line-clamp-2">
                                                {stripHtml(entry.processed_content || entry.raw_content)}
                                            </p>
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
        </div>
    );
}

export default EntryList;
