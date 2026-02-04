import { useState, useEffect } from 'react';
import { getCategories, createCategory, updateCategory, deleteCategory } from '../utils/api';

function CategoryManager() {
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        parent_id: null
    });
    const [editingId, setEditingId] = useState(null);

    useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            setLoading(true);
            const response = await getCategories();
            setCategories(response.data.categories);
        } catch (error) {
            console.error('Error fetching categories:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            if (editingId) {
                await updateCategory(editingId, formData);
            } else {
                await createCategory(formData);
            }

            setFormData({ name: '', description: '', parent_id: null });
            setShowForm(false);
            setEditingId(null);
            fetchCategories();
        } catch (error) {
            console.error('Error saving category:', error);
            alert(error.response?.data?.error || 'Failed to save category');
        }
    };

    const handleEdit = (category) => {
        setFormData({
            name: category.name,
            description: category.description || '',
            parent_id: category.parent_id
        });
        setEditingId(category.id);
        setShowForm(true);
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this category?')) return;

        try {
            await deleteCategory(id);
            fetchCategories();
        } catch (error) {
            console.error('Error deleting category:', error);
            alert('Failed to delete category');
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
        <div className="space-y-6 fade-in">
            <div className="retro-card">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">Category Manager 📁</h2>
                    <button
                        onClick={() => {
                            setShowForm(!showForm);
                            setEditingId(null);
                            setFormData({ name: '', description: '', parent_id: null });
                        }}
                        className="retro-btn-primary"
                    >
                        {showForm ? '❌ Cancel' : '➕ Add Category'}
                    </button>
                </div>

                {/* Form */}
                {showForm && (
                    <div className="mb-6 p-6 bg-blue-50 rounded-lg border-2 border-blue-200">
                        <h3 className="text-lg font-bold mb-4">
                            {editingId ? 'Edit Category' : 'Create New Category'}
                        </h3>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Name *</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                    className="retro-input"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                                    className="retro-input h-20 resize-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Parent Category (for subcategory)</label>
                                <select
                                    value={formData.parent_id || ''}
                                    onChange={(e) => setFormData(prev => ({ ...prev, parent_id: e.target.value ? parseInt(e.target.value) : null }))}
                                    className="retro-select"
                                >
                                    <option value="">None (Top-level category)</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>
                            <button type="submit" className="retro-btn-primary w-full">
                                {editingId ? '💾 Update' : '✅ Create'}
                            </button>
                        </form>
                    </div>
                )}

                {/* Categories List */}
                <div className="space-y-4">
                    {categories.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">No categories yet. Create your first one!</p>
                    ) : (
                        categories.map(category => (
                            <div key={category.id} className="retro-card bg-white">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <h3 className="text-lg font-bold text-gray-800">{category.name}</h3>
                                        {category.description && (
                                            <p className="text-sm text-gray-600 mt-1">{category.description}</p>
                                        )}

                                        {/* Subcategories */}
                                        {category.subcategories && category.subcategories.length > 0 && (
                                            <div className="mt-3 pl-4 border-l-4 border-retro-accent">
                                                <p className="text-xs font-medium text-gray-500 mb-2">Subcategories:</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {category.subcategories.map(sub => (
                                                        <span key={sub.id} className="retro-badge bg-blue-100 text-blue-800">
                                                            {sub.name}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex space-x-2 ml-4">
                                        <button
                                            onClick={() => handleEdit(category)}
                                            className="px-3 py-1 text-sm border-2 border-retro-border rounded hover:bg-gray-100"
                                        >
                                            ✏️ Edit
                                        </button>
                                        <button
                                            onClick={() => handleDelete(category.id)}
                                            className="px-3 py-1 text-sm border-2 border-red-500 text-red-500 rounded hover:bg-red-50"
                                        >
                                            🗑️ Delete
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {categories.length > 0 && (
                    <div className="mt-6 p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                        <p className="text-sm text-yellow-800">
                            ℹ️ Maximum 10 top-level categories allowed. Current: {categories.length}/10
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default CategoryManager;
