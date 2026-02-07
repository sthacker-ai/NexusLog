import { useState, useEffect } from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';

function SystemStatus() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [logs, setLogs] = useState([]);
    const [activeTab, setActiveTab] = useState('bot');
    const [logOffset, setLogOffset] = useState(0);
    const [hasMoreLogs, setHasMoreLogs] = useState(false);
    const [totalLogs, setTotalLogs] = useState(0);
    const [loadingMore, setLoadingMore] = useState(false);
    const [usage, setUsage] = useState(null);

    const LOG_LIMIT = 50;

    const fetchStatus = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/system-status');
            const data = await res.json();
            setStatus(data);
        } catch (error) {
            console.error('Error fetching status:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchUsage = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/usage?days=15');
            const data = await res.json();
            setUsage(data);
        } catch (error) {
            console.error('Error fetching usage:', error);
        }
    };

    // Fetch logs with pagination - latest first
    const fetchLogs = async (service, offset = 0, append = false) => {
        try {
            if (append) setLoadingMore(true);

            const res = await fetch(`http://localhost:5000/api/logs/${service}?offset=${offset}&limit=${LOG_LIMIT}`);
            const data = await res.json();

            if (data.logs && Array.isArray(data.logs)) {
                if (append) {
                    setLogs(prev => [...prev, ...data.logs]);
                } else {
                    setLogs(data.logs);
                }
                setHasMoreLogs(data.has_more || false);
                setTotalLogs(data.total || 0);
                setLogOffset(offset);
            } else {
                if (!append) setLogs([]);
                setHasMoreLogs(false);
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
            if (!append) setLogs([]);
        } finally {
            setLoadingMore(false);
        }
    };

    const loadMoreLogs = () => {
        const newOffset = logOffset + LOG_LIMIT;
        fetchLogs(activeTab, newOffset, true);
    };

    useEffect(() => {
        fetchStatus();
        fetchLogs(activeTab);
        fetchUsage();
        const interval = setInterval(() => {
            fetchStatus();
            // Don't auto-refresh logs if user has scrolled to load more
            if (logOffset === 0) {
                fetchLogs(activeTab);
            }
        }, 300000); // Poll every 5 mins
        return () => clearInterval(interval);
    }, []);

    // Reset and fetch logs when tab changes
    useEffect(() => {
        setLogOffset(0);
        setHasMoreLogs(false);
        fetchLogs(activeTab, 0, false);
    }, [activeTab]);

    if (loading) return <div className="text-center p-8">Loading system stats... 🔄</div>;

    if (!status) return <div className="text-center p-8 text-red-500">Failed to load system status ⚠️</div>;

    const StatusCard = ({ title, info }) => {
        const safeInfo = info || { status: 'unknown', message: 'Service status unavailable' };
        const isOnline = safeInfo.status === 'online';

        return (
            <div className={`p-4 rounded-lg border-2 ${isOnline ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold capitalize">{title}</h3>
                    <span className={`text-2xl ${isOnline ? 'animate-pulse' : ''}`}>{isOnline ? '🟢' : '🔴'}</span>
                </div>
                <p className={`text-sm ${isOnline ? 'text-green-700' : 'text-red-700'}`}>
                    {safeInfo.message}
                </p>
            </div>
        );
    };

    const formatLogLine = (line) => {
        try {
            if (!line) return null;

            const textLine = typeof line === 'string' ? line : JSON.stringify(line);

            const parts = textLine.split(' - ');
            if (parts.length >= 3) {
                const timestamp = parts[0];
                const level = parts[2];
                let levelClass = 'text-gray-700';
                if (level.includes('INFO')) levelClass = 'text-blue-600 font-bold';
                if (level.includes('ERROR')) levelClass = 'text-red-600 font-bold';
                if (level.includes('WARNING')) levelClass = 'text-yellow-600 font-bold';

                return (
                    <div className="font-mono text-xs mb-1 hover:bg-gray-100 p-1 rounded">
                        <span className="text-gray-500 mr-2">[{timestamp}]</span>
                        <span className={`${levelClass} mr-2`}>{level}</span>
                        <span className="text-gray-800 break-words">{parts.slice(3).join(' - ')}</span>
                    </div>
                );
            }
            return <div className="font-mono text-xs text-gray-700 mb-1 hover:bg-gray-100 p-1 rounded break-words">{textLine}</div>;
        } catch (e) {
            console.error("Log formatting error:", e);
            return <div className="text-red-500 text-xs">Error formatting log line</div>;
        }
    };

    // Format large numbers with commas
    const formatNumber = (num) => {
        if (!num) return '0';
        return num.toLocaleString();
    };

    // Format model name for display
    const formatModelName = (model) => {
        if (!model) return 'Unknown';
        // Shorten long model names
        const parts = model.split('/');
        if (parts.length > 1) {
            return parts[parts.length - 1]; // Get just the model name
        }
        return model;
    };

    // Usage Chart Component using Recharts
    const UsageChart = ({ data }) => {
        if (!data || data.length === 0) return null;

        const FREE_LIMIT = 20; // Free tier limit per model per day

        // Transform data for Recharts - reverse so oldest is left
        const chartData = [...data].reverse().map(day => {
            let input = 0, output = 0, requests = 0;
            day.models.forEach(m => {
                input += m.input_tokens || 0;
                output += m.output_tokens || 0;
                requests += m.requests || 0;
            });
            return {
                date: `${parseInt(day.date.slice(5, 7))}/${parseInt(day.date.slice(8, 10))}`,
                inputTokens: input,
                outputTokens: output,
                requests: requests
            };
        });

        return (
            <div className="bg-gray-50 p-4 rounded-lg border-2 border-gray-200">
                <ResponsiveContainer width="100%" height={220}>
                    <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                        <YAxis
                            yAxisId="left"
                            orientation="left"
                            tick={{ fontSize: 10 }}
                            tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
                            label={{ value: 'Tokens', angle: -90, position: 'insideLeft', fontSize: 11 }}
                        />
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            domain={[0, 30]}
                            tick={{ fontSize: 10 }}
                            label={{ value: 'Requests', angle: 90, position: 'insideRight', fontSize: 11 }}
                        />
                        <Tooltip
                            formatter={(value, name) => [
                                name === 'requests' ? value : value.toLocaleString(),
                                name === 'inputTokens' ? 'Input Tokens' :
                                    name === 'outputTokens' ? 'Output Tokens' : 'Requests'
                            ]}
                        />
                        <Legend
                            wrapperStyle={{ fontSize: 10 }}
                            payload={[
                                { value: 'Input Tokens', type: 'square', color: '#22C55E', id: 'inputTokens' },
                                { value: 'Output Tokens', type: 'square', color: '#A855F7', id: 'outputTokens' },
                                { value: 'Requests', type: 'line', color: '#3B82F6', id: 'requests' },
                                { value: `Free Limit (${FREE_LIMIT}/day)`, type: 'plainline', color: '#EF4444', id: 'freeLimit' }
                            ]}
                        />
                        <ReferenceLine
                            yAxisId="right"
                            y={FREE_LIMIT}
                            stroke="#EF4444"
                            strokeDasharray="5 5"
                        />
                        <Bar yAxisId="left" dataKey="inputTokens" fill="#22C55E" barSize={10} />
                        <Bar yAxisId="left" dataKey="outputTokens" fill="#A855F7" barSize={10} />
                        <Line yAxisId="right" type="monotone" dataKey="requests" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        );
    };

    return (
        <div className="max-w-4xl mx-auto fade-in">
            <div className="retro-card mb-8">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold">System Status Dashboard 🎛️</h2>
                    <button onClick={fetchStatus} className="retro-btn-secondary text-sm">🔄 Refresh</button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    <StatusCard title="Database" info={status.database} />
                    <StatusCard title="Gemini AI" info={status.gemini} />
                    <StatusCard title="Replicate" info={status.replicate} />
                    <StatusCard title="Ollama" info={status.ollama} />
                    <StatusCard title="Telegram Bot" info={status.bot} />
                </div>
            </div>

            {/* Logs Section */}
            <div className="retro-card flex flex-col mb-8" style={{ minHeight: '400px' }}>
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-bold">System Logs</h3>
                        {totalLogs > 0 && (
                            <span className="text-xs text-gray-500">
                                (Showing {logs.length} of {totalLogs})
                            </span>
                        )}
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => setActiveTab('bot')}
                            className={`text-xs px-3 py-1 rounded-full border-2 border-black transition-all ${activeTab === 'bot' ? 'bg-retro-accent text-white' : 'bg-gray-100'}`}
                        >
                            Bot
                        </button>
                        <button
                            onClick={() => setActiveTab('backend')}
                            className={`text-xs px-3 py-1 rounded-full border-2 border-black transition-all ${activeTab === 'backend' ? 'bg-retro-accent text-white' : 'bg-gray-100'}`}
                        >
                            Backend
                        </button>
                    </div>
                </div>

                <div className="flex-1 bg-gray-50 border-2 border-gray-200 rounded-lg p-4 overflow-y-auto custom-scrollbar" style={{ maxHeight: '350px' }}>
                    {!logs || !Array.isArray(logs) || logs.length === 0 ? (
                        <p className="text-gray-400 text-center italic">No logs available</p>
                    ) : (
                        <>
                            {logs.map((line, i) => <div key={i}>{formatLogLine(line)}</div>)}

                            {hasMoreLogs && (
                                <div className="text-center mt-4 pt-4 border-t border-gray-200">
                                    <button
                                        onClick={loadMoreLogs}
                                        disabled={loadingMore}
                                        className="retro-btn-secondary text-sm px-6"
                                    >
                                        {loadingMore ? '⏳ Loading...' : '📜 Load More Logs'}
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* AI Usage Section */}
            <div className="retro-card">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-bold">🤖 AI Usage (Last 7 Days)</h3>
                    <button onClick={fetchUsage} className="retro-btn-secondary text-sm">🔄 Refresh</button>
                </div>

                {!usage ? (
                    <p className="text-gray-400 text-center italic py-4">Loading usage data...</p>
                ) : (
                    <>
                        {/* Totals Summary */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200 text-center">
                                <p className="text-2xl font-bold text-blue-600">{formatNumber(usage.totals?.requests)}</p>
                                <p className="text-xs text-gray-600">API Requests</p>
                            </div>
                            <div className="bg-green-50 p-4 rounded-lg border-2 border-green-200 text-center">
                                <p className="text-2xl font-bold text-green-600">{formatNumber(usage.totals?.input_tokens)}</p>
                                <p className="text-xs text-gray-600">Input Tokens</p>
                            </div>
                            <div className="bg-purple-50 p-4 rounded-lg border-2 border-purple-200 text-center">
                                <p className="text-2xl font-bold text-purple-600">{formatNumber(usage.totals?.output_tokens)}</p>
                                <p className="text-xs text-gray-600">Output Tokens</p>
                            </div>
                            <div className="bg-yellow-50 p-4 rounded-lg border-2 border-yellow-200 text-center">
                                <p className="text-2xl font-bold text-yellow-600">${usage.totals?.cost_usd?.toFixed(4) || '0.0000'}</p>
                                <p className="text-xs text-gray-600">Est. Cost (if paid)</p>
                            </div>
                        </div>

                        {/* Usage by Model */}
                        {usage.by_model && usage.by_model.length > 0 && (
                            <div className="mb-6">
                                <h4 className="font-bold text-sm mb-3 text-gray-700">By Model</h4>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b-2 border-gray-200">
                                                <th className="text-left py-2 px-2">Model</th>
                                                <th className="text-right py-2 px-2">Requests</th>
                                                <th className="text-right py-2 px-2">Input</th>
                                                <th className="text-right py-2 px-2">Output</th>
                                                <th className="text-right py-2 px-2">Cost</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {usage.by_model.map((m, i) => (
                                                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                                                    <td className="py-2 px-2 font-mono text-xs">{formatModelName(m.model)}</td>
                                                    <td className="text-right py-2 px-2">{formatNumber(m.requests)}</td>
                                                    <td className="text-right py-2 px-2 text-green-600">{formatNumber(m.input_tokens)}</td>
                                                    <td className="text-right py-2 px-2 text-purple-600">{formatNumber(m.output_tokens)}</td>
                                                    <td className="text-right py-2 px-2 text-yellow-600">${m.cost_usd?.toFixed(4) || '0.0000'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Daily Breakdown */}
                        {usage.daily && usage.daily.length > 0 && (
                            <div>
                                <h4 className="font-bold text-sm mb-3 text-gray-700">Daily Activity</h4>
                                <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
                                    {usage.daily.map((day, i) => (
                                        <div key={i} className="bg-gray-50 p-3 rounded-lg">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-bold text-sm">{day.date}</span>
                                                <span className="text-xs text-gray-500">
                                                    {day.models.reduce((sum, m) => sum + m.requests, 0)} requests
                                                </span>
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {day.models.map((m, j) => (
                                                    <span key={j} className="retro-badge bg-blue-100 text-blue-800 text-xs">
                                                        {formatModelName(m.model)}: {m.requests} req
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Usage Chart */}
                        {usage.daily && usage.daily.length > 0 && (
                            <div className="mt-6">
                                <h4 className="font-bold text-sm mb-3 text-gray-700">📊 Usage Chart (15 Days)</h4>
                                <UsageChart data={usage.daily} />
                            </div>
                        )}

                        {usage.totals?.requests === 0 && (
                            <p className="text-gray-400 text-center italic py-4">No AI usage recorded yet</p>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

export default SystemStatus;
