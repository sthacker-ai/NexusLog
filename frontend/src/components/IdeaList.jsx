import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { getContentIdeas, getCategories } from '../utils/api';
import { formatDateIST } from '../utils/dateUtils';

function IdeaList() {
    const [ideas, setIdeas] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        output_type: '',
        search: ''
    });
    const [expandedId, setExpandedId] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [ideasRes, categoriesRes] = await Promise.all([
                getContentIdeas(),
                getCategories()
            ]);

            setIdeas(ideasRes.data.ideas);
            setCategories(categoriesRes.data.categories);
        } catch (error) {
            console.error('Error fetching ideas:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredIdeas = ideas.filter(idea => {
        const matchesOutputType = !filters.output_type || idea.output_types.includes(filters.output_type);
        const searchText = filters.search.toLowerCase();
        const matchesSearch = !filters.search ||
            (idea.title && idea.title.toLowerCase().includes(searchText)) ||
            idea.idea_description.toLowerCase().includes(searchText);

        return matchesOutputType && matchesSearch;
    });

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
                <h2 className="text-2xl font-bold mb-6">Content Ideas 💡</h2>

                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium mb-2">Search</label>
                        <input
                            type="text"
                            value={filters.search}
                            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                            className="retro-input"
                            placeholder="Search ideas..."
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-2">Filter by Output Type</label>
                        <select
                            value={filters.output_type}
                            onChange={(e) => setFilters(prev => ({ ...prev, output_type: e.target.value }))}
                            className="retro-select"
                        >
                            <option value="">All Types</option>
                            <option value="blog">Blog</option>
                            <option value="youtube">YouTube</option>
                            <option value="linkedin">LinkedIn</option>
                            <option value="shorts">Shorts</option>
                            <option value="reels">Reels</option>
                        </select>
                    </div>
                </div>

                {/* Ideas List */}
                {filteredIdeas.length === 0 ? (
                    <p className="text-gray-500 text-center py-12">No content ideas found. Create one from the Add Entry page!</p>
                ) : (
                    <div className="space-y-4">
                        {filteredIdeas.map((idea) => (
                            <div
                                key={idea.id}
                                className="p-6 bg-white rounded-lg border-2 border-gray-200 hover:border-retro-accent transition-all hover:shadow-retro cursor-pointer"
                                onClick={() => setExpandedId(expandedId === idea.id ? null : idea.id)}
                            >
                                {/* Header with Title */}
                                <div className="mb-3">
                                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                                        {idea.title || idea.idea_description.substring(0, 60) + (idea.idea_description.length > 60 ? '...' : '')}
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {idea.output_types.map(type => (
                                            <span key={type} className={`badge-${type}`}>
                                                {type}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Expanded Content with Colorful Markdown */}
                                {expandedId === idea.id ? (
                                    <div className="mt-4 fade-in">
                                        <div className="idea-content-box p-5 rounded-lg mb-4">
                                            <div className="markdown-content prose prose-sm max-w-none">
                                                <ReactMarkdown>
                                                    {idea.idea_description}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                        <div className="flex justify-end space-x-2">
                                            <button className="retro-btn-secondary text-xs">✏️ Edit</button>
                                            <button className="retro-btn-primary text-xs">🚀 Start Project</button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="bg-gray-50 p-2 rounded border border-gray-200">
                                        <p className="text-xs text-gray-500 truncate">
                                            {idea.idea_description.substring(0, 100)}...
                                        </p>
                                    </div>
                                )}

                                <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                                    <span>Created: {formatDateIST(idea.created_at)}</span>
                                    <span className="retro-badge bg-gray-100 text-gray-700">{idea.status}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default IdeaList;

