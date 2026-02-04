-- Add title column to content_ideas table
ALTER TABLE content_ideas ADD COLUMN IF NOT EXISTS title VARCHAR(200);

-- Update existing records with a generated title from idea_description (first 50 chars)
UPDATE content_ideas 
SET title = LEFT(idea_description, 50) || '...'
WHERE title IS NULL AND idea_description IS NOT NULL;
