import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getEntriesByDate } from '../utils/api';
import { formatToIST, formatTimeIST } from '../utils/dateUtils';

// Type icons mapping
const typeIcons = {
    text: '📝',
    image: '🖼️',
    audio: '🎤',
    video: '🎥',
    link: '🔗'
};

// Helper to strip HTML
const stripHtml = (html) => {
    if (!html) return '';
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
};

// Format date header (e.g., "Today", "Yesterday", "Feb 4, 2026")
const formatDateHeader = (dateStr) => {
    const date = new Date(dateStr + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const entryDate = new Date(date);
    entryDate.setHours(0, 0, 0, 0);

    if (entryDate.getTime() === today.getTime()) {
        return 'Today';
    } else if (entryDate.getTime() === yesterday.getTime()) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString('en-IN', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
        });
    }
};

function Timeline() {
    const [timeline, setTimeline] = useState([]);
    const [loading, setLoading] = useState(true);
    const [totalEntries, setTotalEntries] = useState(0);

    useEffect(() => {
        fetchTimeline();
    }, []);

    const fetchTimeline = async () => {
        try {
            setLoading(true);
            const res = await getEntriesByDate({ days: 30 });
            setTimeline(res.data.timeline);
            setTotalEntries(res.data.total_entries);
        } catch (error) {
            console.error('Error fetching timeline:', error);
        } finally {
            setLoading(false);
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
        <div className="max-w-3xl mx-auto fade-in">
            {/* Header */}
            <div className="retro-card mb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <Link to="/" className="text-retro-accent hover:underline">← Dashboard</Link>
                        <h2 className="text-2xl font-bold">Timeline 📅</h2>
                    </div>
                    <span className="text-gray-500">{totalEntries} entries (last 30 days)</span>
                </div>
            </div>

            {/* Timeline */}
            {timeline.length === 0 ? (
                <div className="retro-card text-center py-12">
                    <p className="text-gray-500">No entries in the last 30 days.</p>
                    <Link to="/add" className="text-retro-accent hover:underline mt-2 inline-block">Add your first entry →</Link>
                </div>
            ) : (
                <div className="relative">
                    {/* Vertical line */}
                    <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300"></div>

                    {timeline.map((day) => (
                        <div key={day.date} className="mb-8">
                            {/* Date Header */}
                            <div className="flex items-center mb-4">
                                <div className="w-12 h-12 rounded-full bg-retro-accent border-4 border-white shadow-md flex items-center justify-center z-10">
                                    <span className="text-white text-lg font-bold">
                                        {new Date(day.date).getDate()}
                                    </span>
                                </div>
                                <div className="ml-4">
                                    <h3 className="text-lg font-bold text-gray-800">
                                        {formatDateHeader(day.date)}
                                    </h3>
                                    <p className="text-xs text-gray-500">
                                        {day.entries.length} {day.entries.length === 1 ? 'entry' : 'entries'}
                                    </p>
                                </div>
                            </div>

                            {/* Entries for this day */}
                            <div className="ml-16 space-y-3">
                                {day.entries.map((entry) => (
                                    <div
                                        key={entry.id}
                                        className="bg-white rounded-lg border-2 border-gray-200 p-4 hover:border-retro-accent transition-all hover:shadow-md"
                                    >
                                        <div className="flex items-start space-x-3">
                                            <span className="text-xl">{typeIcons[entry.content_type] || '📄'}</span>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <span className="text-xs text-gray-500">
                                                        {formatTimeIST(entry.created_at)}
                                                    </span>
                                                    {entry.category && (
                                                        <span className="retro-badge bg-blue-100 text-blue-800 text-xs">
                                                            {entry.category.name}
                                                        </span>
                                                    )}
                                                    {entry.entry_metadata?.is_content_idea && (
                                                        <span className="retro-badge bg-yellow-100 text-yellow-800 text-xs">💡</span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-700 line-clamp-2">
                                                    {stripHtml(entry.processed_content || entry.raw_content)}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Timeline;
