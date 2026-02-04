import { useState, useEffect } from 'react';
import { getConfig, updateConfig } from '../utils/api';

function Settings() {
    const [config, setConfig] = useState({
        ai_provider: { primary: 'gemini', fallback: 'replicate' },
        tts_settings: { voice: 'en-GB-male', provider: 'gemini' }
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        try {
            setLoading(true);
            const response = await getConfig();
            setConfig(response.data.config);
        } catch (error) {
            console.error('Error fetching config:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setSuccess(false);

        try {
            await updateConfig('ai_provider', config.ai_provider);
            await updateConfig('tts_settings', config.tts_settings);

            setSuccess(true);
            setTimeout(() => setSuccess(false), 3000);
        } catch (error) {
            console.error('Error saving config:', error);
            alert('Failed to save settings');
        } finally {
            setSaving(false);
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
        <div className="max-w-3xl mx-auto space-y-6 fade-in">
            <div className="retro-card">
                <h2 className="text-2xl font-bold mb-6">Settings ⚙️</h2>

                {success && (
                    <div className="mb-6 p-4 bg-green-100 border-2 border-green-500 rounded-lg">
                        <p className="text-green-800 font-medium">✅ Settings saved successfully!</p>
                    </div>
                )}

                {/* AI Provider Settings */}
                <div className="mb-8">
                    <h3 className="text-xl font-bold mb-4">AI Provider Configuration</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Primary AI Provider</label>
                            <select
                                value={config.ai_provider?.primary || 'gemini'}
                                onChange={(e) => setConfig(prev => ({
                                    ...prev,
                                    ai_provider: { ...prev.ai_provider, primary: e.target.value }
                                }))}
                                className="retro-select"
                            >
                                <option value="gemini">Google Gemini (Free)</option>
                                <option value="ollama">Ollama (Local)</option>
                                <option value="replicate">Replicate (Paid)</option>
                                <option value="openai">OpenAI (Paid)</option>
                            </select>
                            <p className="text-xs text-gray-600 mt-2">
                                Primary provider for AI tasks like categorization and content generation
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">Fallback Provider</label>
                            <select
                                value={config.ai_provider?.fallback || 'replicate'}
                                onChange={(e) => setConfig(prev => ({
                                    ...prev,
                                    ai_provider: { ...prev.ai_provider, fallback: e.target.value }
                                }))}
                                className="retro-select"
                            >
                                <option value="gemini">Google Gemini</option>
                                <option value="ollama">Ollama</option>
                                <option value="replicate">Replicate</option>
                                <option value="openai">OpenAI</option>
                            </select>
                            <p className="text-xs text-gray-600 mt-2">
                                Used when primary provider fails or is unavailable
                            </p>
                        </div>
                    </div>
                </div>

                {/* TTS Settings */}
                <div className="mb-8">
                    <h3 className="text-xl font-bold mb-4">Text-to-Speech Settings</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Voice</label>
                            <select
                                value={config.tts_settings?.voice || 'en-GB-male'}
                                onChange={(e) => setConfig(prev => ({
                                    ...prev,
                                    tts_settings: { ...prev.tts_settings, voice: e.target.value }
                                }))}
                                className="retro-select"
                            >
                                <option value="en-GB-male">British Male (Default)</option>
                                <option value="en-US-male">American Male</option>
                                <option value="en-GB-female">British Female</option>
                                <option value="en-US-female">American Female</option>
                            </select>
                            <p className="text-xs text-gray-600 mt-2">
                                Voice for Telegram bot responses
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">TTS Provider</label>
                            <select
                                value={config.tts_settings?.provider || 'gemini'}
                                onChange={(e) => setConfig(prev => ({
                                    ...prev,
                                    tts_settings: { ...prev.tts_settings, provider: e.target.value }
                                }))}
                                className="retro-select"
                            >
                                <option value="gemini">Google Gemini</option>
                                <option value="replicate">Replicate</option>
                                <option value="openai">OpenAI</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* API Keys Info */}
                <div className="mb-8 p-6 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                    <h3 className="text-lg font-bold mb-3">🔑 API Keys Configuration</h3>
                    <p className="text-sm text-gray-700 mb-3">
                        API keys are configured via environment variables for security.
                        Update your <code className="px-2 py-1 bg-white rounded border">.env</code> file with:
                    </p>
                    <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                        <li><code>GOOGLE_AI_API_KEY</code> - For Gemini</li>
                        <li><code>OLLAMA_BASE_URL</code> - For local Ollama</li>
                        <li><code>REPLICATE_API_KEY</code> - For Replicate</li>
                        <li><code>OPENAI_API_KEY</code> - For OpenAI</li>
                    </ul>
                </div>

                {/* Telegram Bot Status */}
                <div className="mb-8 p-6 bg-blue-50 rounded-lg border-2 border-blue-200">
                    <h3 className="text-lg font-bold mb-3">📱 Telegram Bot</h3>
                    <p className="text-sm text-gray-700 mb-2">
                        Bot Token: <code className="px-2 py-1 bg-white rounded border">Configured via .env</code>
                    </p>
                    <p className="text-xs text-gray-600">
                        Run the bot with: <code className="px-2 py-1 bg-white rounded border">python backend/telegram_bot.py</code>
                    </p>
                </div>

                {/* Save Button */}
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="retro-btn-primary w-full"
                >
                    {saving ? 'Saving...' : '💾 Save Settings'}
                </button>
            </div>

            {/* System Info */}
            <div className="retro-card">
                <h3 className="text-xl font-bold mb-4">System Information</h3>
                <div className="space-y-2 text-sm">
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                        <span className="font-medium">Version:</span>
                        <span>1.0.0</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                        <span className="font-medium">Database:</span>
                        <span>PostgreSQL</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                        <span className="font-medium">Backend:</span>
                        <span>Flask (Python)</span>
                    </div>
                    <div className="flex justify-between p-3 bg-gray-50 rounded">
                        <span className="font-medium">Frontend:</span>
                        <span>React + Vite + Tailwind</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Settings;
