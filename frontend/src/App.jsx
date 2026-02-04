import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState } from 'react';
import Dashboard from './components/Dashboard';
import CategoryManager from './components/CategoryManager';
import ManualInput from './components/ManualInput';
import IdeaList from './components/IdeaList';
import Settings from './components/Settings';
import SystemStatus from './components/SystemStatus';

function App() {
    const [currentPage, setCurrentPage] = useState('dashboard');

    return (
        <Router>
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

                            <nav className="hidden md:flex space-x-2">
                                <Link to="/" className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${currentPage === 'dashboard' ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'}`} onClick={() => setCurrentPage('dashboard')}>
                                    Dashboard
                                </Link>
                                <Link to="/add" className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${currentPage === 'add' ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'}`} onClick={() => setCurrentPage('add')}>
                                    Add Entry
                                </Link>
                                <Link to="/ideas" className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${currentPage === 'ideas' ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'}`} onClick={() => setCurrentPage('ideas')}>
                                    Ideas
                                </Link>
                                <Link to="/categories" className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${currentPage === 'categories' ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'}`} onClick={() => setCurrentPage('categories')}>
                                    Categories
                                </Link>
                                <Link to="/status" className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${currentPage === 'status' ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'}`} onClick={() => setCurrentPage('status')}>
                                    System Status
                                </Link>
                                <Link to="/settings" className={`px-4 py-2 rounded-lg border-2 border-retro-border transition-all ${currentPage === 'settings' ? 'bg-retro-accent text-white' : 'bg-white hover:bg-gray-100'}`} onClick={() => setCurrentPage('settings')}>
                                    Settings
                                </Link>
                            </nav>
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="container mx-auto px-4 py-8">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/add" element={<ManualInput />} />
                        <Route path="/ideas" element={<IdeaList />} />
                        <Route path="/categories" element={<CategoryManager />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="/status" element={<SystemStatus />} />
                    </Routes>
                </main>

                {/* Footer */}
                <footer className="bg-retro-card border-t-4 border-retro-border mt-12 py-6">
                    <div className="container mx-auto px-4 text-center text-sm text-gray-600">
                        <p>Made with 🧠 by NexusLog | Powered by AI</p>
                    </div>
                </footer>
            </div>
        </Router>
    );
}

export default App;
