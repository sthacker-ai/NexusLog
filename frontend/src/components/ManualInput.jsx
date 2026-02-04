import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { createEntry, getCategories } from '../utils/api';

function ManualInput() {
    const [formData, setFormData] = useState({
        content: '',
        content_type: 'text',
        category_id: '',
        subcategory_id: '',
        is_content_idea: false,
        output_types: [],
        use_ai: false
    });

    const [categories, setCategories] = useState([]);
    const [subcategories, setSubcategories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');
    const [isFullscreen, setIsFullscreen] = useState(false); // New state for expand mode

    // Custom Toolbar for Quill
    const modules = {
        toolbar: [
            [{ 'header': [1, 2, false] }],
            ['bold', 'italic', 'underline', 'strike'],
            [{ 'list': 'ordered' }, { 'list': 'bullet' }],
            ['link', 'image'],
            ['clean']
        ],
    };

    const outputTypeOptions = ['blog', 'youtube', 'linkedin', 'shorts', 'reels'];

    useEffect(() => {
        fetchCategories();
    }, []);

    useEffect(() => {
        if (formData.category_id) {
            const selectedCategory = categories.find(cat => cat.id === parseInt(formData.category_id));
            setSubcategories(selectedCategory?.subcategories || []);
        } else {
            setSubcategories([]);
        }
    }, [formData.category_id, categories]);

    const fetchCategories = async () => {
        try {
            const response = await getCategories();
            setCategories(response.data.categories);
        } catch (error) {
            console.error('Error fetching categories:', error);
        }
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleOutputTypeToggle = (type) => {
        setFormData(prev => ({
            ...prev,
            output_types: prev.output_types.includes(type)
                ? prev.output_types.filter(t => t !== type)
                : [...prev.output_types, type]
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.content.trim()) {
            setError('Content is required');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess(false);

        try {
            // If no category selected, find and use "General Notes" category
            let submitData = { ...formData };
            if (!submitData.category_id) {
                const generalNotes = categories.find(cat =>
                    cat.name.toLowerCase() === 'general notes' ||
                    cat.name.toLowerCase() === 'general'
                );
                if (generalNotes) {
                    submitData.category_id = generalNotes.id;
                }
            }

            await createEntry(submitData);
            setSuccess(true);

            // Reset form
            setFormData({
                content: '',
                content_type: 'text',
                category_id: '',
                subcategory_id: '',
                is_content_idea: false,
                output_types: [],
                use_ai: false
            });

            setTimeout(() => setSuccess(false), 3000);
        } catch (error) {
            setError('Failed to create entry. Please try again.');
            console.error('Error creating entry:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto fade-in">
            <div className="retro-card">
                <h2 className="text-2xl font-bold mb-6">Add New Entry ✍️</h2>

                {success && (
                    <div className="mb-6 p-4 bg-green-100 border-2 border-green-500 rounded-lg">
                        <p className="text-green-800 font-medium">✅ Entry created successfully!</p>
                    </div>
                )}

                {error && (
                    <div className="mb-6 p-4 bg-red-100 border-2 border-red-500 rounded-lg">
                        <p className="text-red-800 font-medium">❌ {error}</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Content (Rich Text) */}
                    {isFullscreen && createPortal(
                        /* Fullscreen mode - rendered via portal to prevent flicker */
                        <div className="fullscreen-editor-container" onClick={(e) => e.stopPropagation()}>
                            <div className="flex justify-between items-center mb-3">
                                <label className="text-lg font-bold">Content *</label>
                                <button
                                    type="button"
                                    onClick={() => setIsFullscreen(false)}
                                    className="text-sm px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                                >
                                    ↙️ Minimize
                                </button>
                            </div>

                            {/* Success/Error feedback in fullscreen */}
                            {success && (
                                <div className="mb-3 p-3 bg-green-100 border-2 border-green-500 rounded-lg">
                                    <p className="text-green-800 font-medium">✅ Entry created successfully!</p>
                                </div>
                            )}
                            {error && (
                                <div className="mb-3 p-3 bg-red-100 border-2 border-red-500 rounded-lg">
                                    <p className="text-red-800 font-medium">❌ {error}</p>
                                </div>
                            )}

                            <div className="flex-1 bg-white rounded-lg border-2 border-retro-border flex flex-col min-h-0 quill-wrapper" style={{ maxHeight: 'calc(100vh - 220px)' }}>
                                <ReactQuill
                                    theme="snow"
                                    value={formData.content}
                                    onChange={(content) => setFormData(prev => ({ ...prev, content }))}
                                    modules={modules}
                                    className="flex-1"
                                    placeholder="Write something amazing..."
                                />
                            </div>

                            <div className="mt-4 flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setIsFullscreen(false)}
                                    className="retro-btn-secondary"
                                >
                                    ↙️ Done Writing
                                </button>
                                <button
                                    type="button"
                                    disabled={loading}
                                    onClick={handleSubmit}
                                    className="retro-btn-primary"
                                >
                                    {loading ? 'Creating...' : '✅ Create Entry'}
                                </button>
                            </div>
                        </div>,
                        document.body
                    )}

                    {/* Normal mode - always rendered but hidden when fullscreen */}
                    {!isFullscreen && (
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <label className="block text-sm font-medium">Content *</label>
                                <button
                                    type="button"
                                    onClick={() => setIsFullscreen(true)}
                                    className="text-sm px-3 py-1 bg-retro-accent text-white rounded hover:bg-opacity-90 transition-colors"
                                >
                                    ↗️ Expand
                                </button>
                            </div>

                            <div className="bg-white rounded-lg border-2 border-retro-border quill-wrapper">
                                <ReactQuill
                                    theme="snow"
                                    value={formData.content}
                                    onChange={(content) => setFormData(prev => ({ ...prev, content }))}
                                    modules={modules}
                                    className="h-64"
                                    placeholder="Write something amazing..."
                                />
                            </div>
                        </div>
                    )}

                    {/* Content Type */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Content Type</label>
                        <select
                            name="content_type"
                            value={formData.content_type}
                            onChange={handleInputChange}
                            className="retro-select"
                        >
                            <option value="text">📝 Text</option>
                            <option value="image">🖼️ Image</option>
                            <option value="audio">🎤 Audio</option>
                            <option value="video">🎥 Video</option>
                            <option value="link">🔗 Link</option>
                        </select>
                    </div>

                    {/* Category */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Category</label>
                            <select
                                name="category_id"
                                value={formData.category_id}
                                onChange={handleInputChange}
                                className="retro-select"
                            >
                                <option value="">Select category...</option>
                                {categories.map(cat => (
                                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                                ))}
                            </select>
                        </div>

                        {/* Subcategory */}
                        {subcategories.length > 0 && (
                            <div>
                                <label className="block text-sm font-medium mb-2">Subcategory</label>
                                <select
                                    name="subcategory_id"
                                    value={formData.subcategory_id}
                                    onChange={handleInputChange}
                                    className="retro-select"
                                >
                                    <option value="">Select subcategory...</option>
                                    {subcategories.map(sub => (
                                        <option key={sub.id} value={sub.id}>{sub.name}</option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>

                    {/* Content Idea Checkbox */}
                    <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
                        <input
                            type="checkbox"
                            name="is_content_idea"
                            checked={formData.is_content_idea}
                            onChange={handleInputChange}
                            className="retro-checkbox"
                            id="is_content_idea"
                        />
                        <label htmlFor="is_content_idea" className="font-medium cursor-pointer">
                            💡 This is a content creation idea
                        </label>
                    </div>

                    {/* Output Types (only if content idea) */}
                    {formData.is_content_idea && (
                        <div>
                            <label className="block text-sm font-medium mb-3">Output Types</label>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {outputTypeOptions.map(type => (
                                    <div
                                        key={type}
                                        onClick={() => handleOutputTypeToggle(type)}
                                        className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${formData.output_types.includes(type)
                                            ? 'bg-retro-accent text-white border-retro-accent'
                                            : 'bg-white border-gray-300 hover:border-retro-accent'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-2">
                                            <input
                                                type="checkbox"
                                                checked={formData.output_types.includes(type)}
                                                onChange={() => { }}
                                                className="retro-checkbox"
                                            />
                                            <span className="capitalize font-medium">{type}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* AI Validation Checkbox */}
                    <div className="flex items-center space-x-3 p-4 bg-purple-50 rounded-lg border-2 border-purple-200">
                        <input
                            type="checkbox"
                            name="use_ai"
                            checked={formData.use_ai}
                            onChange={handleInputChange}
                            className="retro-checkbox"
                            id="use_ai"
                        />
                        <label htmlFor="use_ai" className="font-medium cursor-pointer">
                            🤖 Use AI to validate and suggest category
                        </label>
                    </div>

                    {/* Submit Button */}
                    <div className="flex space-x-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="retro-btn-primary flex-1"
                        >
                            {loading ? 'Creating...' : '✅ Create Entry'}
                        </button>
                        <button
                            type="button"
                            onClick={() => setFormData({
                                content: '',
                                content_type: 'text',
                                category_id: '',
                                subcategory_id: '',
                                is_content_idea: false,
                                output_types: [],
                                use_ai: false
                            })}
                            className="retro-btn-secondary"
                        >
                            🔄 Reset
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default ManualInput;
