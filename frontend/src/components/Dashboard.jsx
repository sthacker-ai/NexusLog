import { useState, useEffect } from 'react';
import { getStats, getEntries } from '../utils/api';

// Helper to strip HTML tags and decode entities for preview display
const stripHtml = (html) => {
    if (!html) return '';
    // Create temp element to decode HTML entities
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
};

function Dashboard() {
    const [stats, setStats] = useState(null);
    const [recentEntries, setRecentEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedEntryId, setExpandedEntryId] = useState(null);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            const [statsRes, entriesRes] = await Promise.all([
                getStats(),
                getEntries({ limit: 5 })
            ]);

            setStats(statsRes.data);
            setRecentEntries(entriesRes.data.entries);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
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
        <div className="space-y-8 fade-in">
            {/* Welcome Section */}
            <div className="retro-card">
                <h2 className="text-2xl font-bold mb-2">Welcome to NexusLog! 🧠</h2>
                <p className="text-gray-600">Your AI-powered idea management system</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="retro-card bg-blue-50">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Total Entries</p>
                            <p className="text-3xl font-bold text-retro-accent">{stats?.total_entries || 0}</p>
                        </div>
                        <div className="text-4xl">📝</div>
                    </div>
                </div>

                <div className="retro-card bg-green-50">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Content Ideas</p>
                            <p className="text-3xl font-bold text-retro-success">{stats?.total_ideas || 0}</p>
                        </div>
                        <div className="text-4xl">💡</div>
                    </div>
                </div>

                <div className="retro-card bg-purple-50">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Projects</p>
                            <p className="text-3xl font-bold text-purple-600">{stats?.total_projects || 0}</p>
                        </div>
                        <div className="text-4xl">🚀</div>
                    </div>
                </div>

                <div className="retro-card bg-yellow-50">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Categories</p>
                            <p className="text-3xl font-bold text-yellow-600">{stats?.total_categories || 0}</p>
                        </div>
                        <div className="text-4xl">📁</div>
                    </div>
                </div>
            </div>

            {/* Content Type Breakdown */}
            <div className="retro-card">
                <h3 className="text-xl font-bold mb-4">Entries by Type</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {stats?.entries_by_type && Object.entries(stats.entries_by_type).map(([type, count]) => (
                        <div key={type} className="text-center p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                            <p className="text-2xl mb-2">
                                {type === 'text' && '📝'}
                                {type === 'image' && '🖼️'}
                                {type === 'audio' && '🎤'}
                                {type === 'video' && '🎥'}
                                {type === 'link' && '🔗'}
                            </p>
                            <p className="text-lg font-bold">{count}</p>
                            <p className="text-xs text-gray-600 capitalize">{type}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recent Entries */}
            <div className="retro-card">
                <h3 className="text-xl font-bold mb-4">Recent Entries</h3>
                {recentEntries.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No entries yet. Start by adding one!</p>
                ) : (
                    <div className="space-y-3">
                        {recentEntries.map((entry) => (
                            <div
                                key={entry.id}
                                className="p-4 bg-gray-50 rounded-lg border-2 border-gray-200 hover:border-retro-accent transition-all cursor-pointer"
                                onClick={() => setExpandedEntryId(expandedEntryId === entry.id ? null : entry.id)}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <span className="text-lg">
                                                {entry.content_type === 'text' && '📝'}
                                                {entry.content_type === 'image' && '🖼️'}
                                                {entry.content_type === 'audio' && '🎤'}
                                                {entry.content_type === 'video' && '🎥'}
                                                {entry.content_type === 'link' && '🔗'}
                                            </span>
                                            {entry.category && (
                                                <span className="retro-badge bg-blue-100 text-blue-800">
                                                    {entry.category.name}
                                                </span>
                                            )}
                                            {entry.content_type === 'audio' && (
                                                <span className="text-xs text-gray-500 italic ml-2"> (Voice Note)</span>
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
                                                {entry.entry_metadata?.is_content_idea && (
                                                    <span className="retro-badge bg-yellow-100 text-yellow-800 text-xs">Idea generated</span>
                                                )}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-gray-700 line-clamp-2">
                                                {stripHtml(entry.processed_content || entry.raw_content)}
                                            </p>
                                        )}

                                        <p className="text-xs text-gray-500 mt-2">
                                            {new Date(entry.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Quick Actions */}
            <div className="retro-card">
                <h3 className="text-xl font-bold mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <a href="/add" className="retro-btn-primary text-center">
                        ➕ Add New Entry
                    </a>
                    <a href="/ideas" className="retro-btn-secondary text-center">
                        💡 View Ideas
                    </a>
                    <a href="/categories" className="retro-btn-secondary text-center">
                        📁 Manage Categories
                    </a>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
