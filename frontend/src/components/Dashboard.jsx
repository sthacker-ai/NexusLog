import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getStats, getEntries, getAnalytics } from '../utils/api';
import { formatToIST } from '../utils/dateUtils';

// Helper to strip HTML tags and decode entities for preview display
const stripHtml = (html) => {
    if (!html) return '';
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
};

function Dashboard() {
    const [stats, setStats] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [recentEntries, setRecentEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedEntryId, setExpandedEntryId] = useState(null);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            const [statsRes, entriesRes, analyticsRes] = await Promise.all([
                getStats(),
                getEntries({ limit: 5 }),
                getAnalytics()
            ]);

            setStats(statsRes.data);
            setRecentEntries(entriesRes.data.entries);
            setAnalytics(analyticsRes.data);
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

    // Clickable stat tile component
    const StatTile = ({ to, bgColor, label, value, emoji, textColor }) => (
        <Link to={to} className={`retro-card ${bgColor} hover:scale-105 transition-transform cursor-pointer block`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-gray-600 mb-1">{label}</p>
                    <p className={`text-3xl font-bold ${textColor}`}>{value}</p>
                </div>
                <div className="text-4xl">{emoji}</div>
            </div>
        </Link>
    );

    // Clickable type tile component
    const TypeTile = ({ type, count, emoji }) => (
        <Link
            to={`/entries?type=${type}`}
            className="text-center p-4 bg-gray-50 rounded-lg border-2 border-gray-200 hover:border-retro-accent hover:scale-105 transition-all cursor-pointer block"
        >
            <p className="text-2xl mb-2">{emoji}</p>
            <p className="text-lg font-bold">{count}</p>
            <p className="text-xs text-gray-600 capitalize">{type}</p>
        </Link>
    );

    // Simple bar chart component
    const ActivityChart = ({ data }) => {
        if (!data || data.length === 0) return null;
        const maxCount = Math.max(...data.map(d => d.count), 1);

        return (
            <div className="flex items-end justify-between h-32 gap-2">
                {data.map((day) => (
                    <div key={day.date} className="flex-1 flex flex-col items-center">
                        <span className="text-xs text-gray-600 mb-1">{day.count}</span>
                        <div
                            className="w-full bg-retro-accent rounded-t transition-all hover:bg-purple-600"
                            style={{
                                height: `${Math.max((day.count / maxCount) * 100, 5)}%`,
                                minHeight: day.count > 0 ? '8px' : '4px'
                            }}
                        ></div>
                        <span className="text-xs text-gray-500 mt-1">{day.day}</span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="space-y-8 fade-in">
            {/* Welcome Section */}
            <div className="retro-card">
                <h2 className="text-2xl font-bold mb-2">Welcome to NexusLog! 🧠</h2>
                <p className="text-gray-600">Your AI-powered idea management system</p>
            </div>

            {/* Stats Grid - Clickable Tiles */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatTile
                    to="/entries"
                    bgColor="bg-blue-50"
                    label="Total Entries"
                    value={stats?.total_entries || 0}
                    emoji="📝"
                    textColor="text-retro-accent"
                />
                <StatTile
                    to="/ideas"
                    bgColor="bg-green-50"
                    label="Content Ideas"
                    value={stats?.total_ideas || 0}
                    emoji="💡"
                    textColor="text-retro-success"
                />
                <StatTile
                    to="/entries"
                    bgColor="bg-purple-50"
                    label="Projects"
                    value={stats?.total_projects || 0}
                    emoji="🚀"
                    textColor="text-purple-600"
                />
                <StatTile
                    to="/categories"
                    bgColor="bg-yellow-50"
                    label="Categories"
                    value={stats?.total_categories || 0}
                    emoji="📁"
                    textColor="text-yellow-600"
                />
            </div>

            {/* Analytics Section */}
            {analytics && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Activity Chart */}
                    <div className="retro-card">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-bold">📊 Activity (Last 7 Days)</h3>
                            <div className="text-right">
                                <p className="text-2xl font-bold text-retro-accent">{analytics.weekly_total}</p>
                                <p className="text-xs text-gray-500">entries this week</p>
                            </div>
                        </div>
                        <ActivityChart data={analytics.last_7_days} />
                        <p className="text-center text-sm text-gray-500 mt-3">
                            Daily average: <span className="font-bold">{analytics.daily_average}</span> entries
                        </p>
                    </div>

                    {/* Usage Breakdown */}
                    <div className="retro-card">
                        <h3 className="text-xl font-bold mb-4">📈 Usage Insights</h3>

                        {/* Text vs Voice */}
                        <div className="mb-6">
                            <p className="text-sm text-gray-600 mb-2">Text vs Voice Entries</p>
                            <div className="flex items-center space-x-4">
                                <div className="flex-1">
                                    <div className="flex justify-between text-sm mb-1">
                                        <span>📝 Text</span>
                                        <span className="font-bold">{analytics.text_vs_voice?.text || 0}</span>
                                    </div>
                                    <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-blue-500 rounded-full"
                                            style={{
                                                width: `${analytics.text_vs_voice?.text / (analytics.text_vs_voice?.text + analytics.text_vs_voice?.audio + 1) * 100}%`
                                            }}
                                        ></div>
                                    </div>
                                </div>
                                <div className="flex-1">
                                    <div className="flex justify-between text-sm mb-1">
                                        <span>🎤 Voice</span>
                                        <span className="font-bold">{analytics.text_vs_voice?.audio || 0}</span>
                                    </div>
                                    <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-green-500 rounded-full"
                                            style={{
                                                width: `${analytics.text_vs_voice?.audio / (analytics.text_vs_voice?.text + analytics.text_vs_voice?.audio + 1) * 100}%`
                                            }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Top Categories */}
                        <div>
                            <p className="text-sm text-gray-600 mb-2">Top Categories (30 days)</p>
                            {analytics.top_categories && analytics.top_categories.length > 0 ? (
                                <div className="space-y-2">
                                    {analytics.top_categories.slice(0, 4).map((cat, i) => (
                                        <div key={cat.name} className="flex items-center justify-between text-sm">
                                            <span className="flex items-center space-x-2">
                                                <span className="text-gray-400">{i + 1}.</span>
                                                <span>{cat.name}</span>
                                            </span>
                                            <span className="retro-badge bg-gray-100">{cat.count}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-400 text-sm italic">No category data yet</p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Content Type Breakdown - Clickable Tiles */}
            <div className="retro-card">
                <h3 className="text-xl font-bold mb-4">Entries by Type</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {stats?.entries_by_type && Object.entries(stats.entries_by_type).map(([type, count]) => (
                        <TypeTile
                            key={type}
                            type={type}
                            count={count}
                            emoji={
                                type === 'text' ? '📝' :
                                    type === 'image' ? '🖼️' :
                                        type === 'audio' ? '🎤' :
                                            type === 'video' ? '🎥' :
                                                type === 'link' ? '🔗' : '📄'
                            }
                        />
                    ))}
                </div>
            </div>

            {/* Recent Entries */}
            <div className="retro-card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold">Recent Entries</h3>
                    <Link to="/entries" className="text-sm text-retro-accent hover:underline">View All →</Link>
                </div>
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

export default Dashboard;
