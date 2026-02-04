import { useState, useEffect } from 'react';

function SystemStatus() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [logs, setLogs] = useState([]);
    const [activeTab, setActiveTab] = useState('bot');

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

    // Fetch logs based on selected tab
    const fetchLogs = async (service) => {
        try {
            const res = await fetch(`http://localhost:5000/api/logs/${service}`);
            const data = await res.json();
            if (data.logs && Array.isArray(data.logs)) {
                // Get last 50 lines in chronological order
                const lastLines = data.logs.slice(-50);
                setLogs(lastLines);
            } else {
                setLogs([]);
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
            setLogs([]);
        }
    };

    useEffect(() => {
        fetchStatus();
        fetchLogs(activeTab);
        const interval = setInterval(() => {
            fetchStatus();
            fetchLogs(activeTab);
        }, 300000); // Poll every 5 mins
        return () => clearInterval(interval);
    }, []);

    // Fetch logs when tab changes
    useEffect(() => {
        fetchLogs(activeTab);
    }, [activeTab]);

    if (loading) return <div className="text-center p-8">Loading system stats... 🔄</div>;

    if (!status) return <div className="text-center p-8 text-red-500">Failed to load system status ⚠️</div>;

    const StatusCard = ({ title, info }) => {
        // Guard against missing info object
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

            // Handle non-string logs
            const textLine = typeof line === 'string' ? line : JSON.stringify(line);

            // Basic timestamp/level coloring
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

            <div className="retro-card h-96 flex flex-col">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold">System Logs</h3>
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

                <div className="flex-1 bg-gray-50 border-2 border-gray-200 rounded-lg p-4 overflow-y-auto custom-scrollbar">
                    {!logs || !Array.isArray(logs) || logs.length === 0 ? (
                        <p className="text-gray-400 text-center italic">No logs available</p>
                    ) : (
                        logs.map((line, i) => <div key={i}>{formatLogLine(line)}</div>)
                    )}
                </div>
            </div>
        </div>
    );
}

export default SystemStatus;
