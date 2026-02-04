-- Add usage_logs table for cost tracking
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    provider VARCHAR(50), -- gemini, replicate, ollama
    model VARCHAR(100),
    feature VARCHAR(50), -- tts, stt, chat, ocr
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    details JSONB
);

-- Index for faster querying by timestamp
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
