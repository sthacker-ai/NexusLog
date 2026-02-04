-- ========================================
-- NexusLog Database Schema
-- ========================================
-- PostgreSQL initialization script
-- Run this after creating the 'nexuslog' database

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create entries table (stores raw and processed content)
CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    raw_content TEXT,
    processed_content TEXT,
    content_type VARCHAR(50) NOT NULL, -- text, image, video, audio, link
    file_path VARCHAR(500),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    subcategory_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    source VARCHAR(50) DEFAULT 'telegram',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create content_ideas table
CREATE TABLE IF NOT EXISTS content_ideas (
    id SERIAL PRIMARY KEY,
    entry_id INTEGER REFERENCES entries(id) ON DELETE CASCADE,
    idea_description TEXT NOT NULL,
    ai_prompt TEXT,
    output_types JSONB DEFAULT '[]', -- ["blog", "youtube", "linkedin", "shorts", "reels"]
    status VARCHAR(50) DEFAULT 'idea',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    tasks JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'idea',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create config table (for app configuration)
CREATE TABLE IF NOT EXISTS config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category_id);
CREATE INDEX IF NOT EXISTS idx_entries_subcategory ON entries(subcategory_id);
CREATE INDEX IF NOT EXISTS idx_entries_created_at ON entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_ideas_entry ON content_ideas(entry_id);
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category_id);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);

-- Insert default categories
INSERT INTO categories (name, description) VALUES
    ('Content Ideas', 'Ideas for blog posts, videos, and social media content'),
    ('VibeCoding Projects', 'Coding projects and automation ideas'),
    ('Stock Trading', 'Stock market ideas and trading strategies'),
    ('General Notes', 'Miscellaneous notes and thoughts')
ON CONFLICT (name) DO NOTHING;

-- Insert default config
INSERT INTO config (key, value) VALUES
    ('ai_provider', '{"primary": "gemini", "fallback": "replicate"}'),
    ('tts_settings', '{"voice": "en-GB-male", "provider": "gemini"}'),
    ('category_limit', '{"max_categories": 10}')
ON CONFLICT (key) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entries_updated_at BEFORE UPDATE ON entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_ideas_updated_at BEFORE UPDATE ON content_ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
