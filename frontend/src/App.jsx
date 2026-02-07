import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import CategoryManager from './components/CategoryManager';
import ManualInput from './components/ManualInput';
import IdeaList from './components/IdeaList';
import EntryList from './components/EntryList';
import Timeline from './components/Timeline';
import Settings from './components/Settings';
import SystemStatus from './components/SystemStatus';

// Navigation component with refresh-on-reclick functionality
function Navigation({ refreshKey, onNavClick }) {
    const location = useLocation();
    const navigate = useNavigate();

    const isActive = (path) => {
        if (path === '/') return location.pathname === '/';
        return location.pathname === path;
    };

    const handleNavClick = (path, pageName, e) => {
        // If already on this page, prevent default and trigger refresh
        if (isActive(path)) {
            e.preventDefault();
            onNavClick(pageName);
        }
    };

    const navItems = [
        { path: '/', label: 'Dashboard', page: 'dashboard' },
        { path: '/add', label: 'Add Entry', page: 'add' },
        { path: '/timeline', label: 'Timeline', page: 'timeline' },
        { path: '/ideas', label: 'Ideas', page: 'ideas' },
        { path: '/categories', label: 'Categories', page: 'categories' },
        { path: '/status', label: 'System Status', page: 'status' },
        { path: '/settings', label: 'Settings', page: 'settings' },
    ];

    return (
        <nav className="hidden md:flex space-x-2">
            {navItems.map(({ path, label, page }) => (
                <Link
                    key={path}
                    to={path}
                    className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${isActive(path) ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'
                        }`}
                    onClick={(e) => handleNavClick(path, page, e)}
                >
                    {label}
                </Link>
            ))}
        </nav>
    );
}

function AppContent() {
    // Refresh key increments to force component remount
    const [refreshKey, setRefreshKey] = useState(0);

    const handleNavClick = useCallback(() => {
        // Increment key to force component refresh
        setRefreshKey(prev => prev + 1);
    }, []);

    return (
        <div className="min-h-screen bg-retro-bg">
            {/* Header */}
            <header className="bg-retro-card border-b-4 border-retro-border shadow-retro sticky top-0 z-50">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <Link to="/" className="w-14 h-14 bg-retro-accent border-2 border-retro-border rounded-lg flex items-center justify-center hover:scale-105 transition-transform cursor-pointer">
                                <span className="text-3xl animate-bounce-slow">🧠</span>
                            </Link>
                            <div>
                                <h1 className="pixel-header text-3xl text-retro-accent tracking-wider">NEXUSLOG</h1>
                                <p className="text-xs text-gray-600 font-mono">Your Neural Nexus for Ideas</p>
                            </div>
                        </div>

                        <Navigation refreshKey={refreshKey} onNavClick={handleNavClick} />
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
                <Routes>
                    <Route path="/" element={<Dashboard key={refreshKey} />} />
                    <Route path="/add" element={<ManualInput key={refreshKey} />} />
                    <Route path="/timeline" element={<Timeline key={refreshKey} />} />
                    <Route path="/ideas" element={<IdeaList key={refreshKey} />} />
                    <Route path="/entries" element={<EntryList key={refreshKey} />} />
                    <Route path="/categories" element={<CategoryManager key={refreshKey} />} />
                    <Route path="/settings" element={<Settings key={refreshKey} />} />
                    <Route path="/status" element={<SystemStatus key={refreshKey} />} />
                </Routes>
            </main>

            {/* Footer */}
            <footer className="bg-retro-card border-t-4 border-retro-border mt-12 py-6">
                <div className="container mx-auto px-4 text-center text-sm text-gray-600">
                    <p>Made with 🧠 by NexusLog | Powered by AI</p>
                </div>
            </footer>
        </div>
    );
}

function App() {
    return (
        <Router>
            <AppContent />
        </Router>
    );
}

export default App;

