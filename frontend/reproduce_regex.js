// Test extractVideoUrl against actual database content
const extractVideoUrl = (text) => {
    if (!text) return null;
    const videoRegex = /(https?:\/\/(?:[a-zA-Z0-9-]+\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/|vimeo\.com\/|dailymotion\.com\/|twitch\.tv\/)[^\s\)]+)|(https?:\/\/[^\s\)]+\.(?:mp4|webm|ogg))/i;
    const match = text.match(videoRegex);
    return match ? match[0] : null;
};

// Actual content from database entries
const testCases = [
    {
        id: 83,
        content: `YouTube Video Title: Claude Opus 4.6 vs GPT-5.3 Codex: How I shipped 93,000 lines of code in 5 days
Channel: How I AI
Duration: 30 minutes
URL: https://www.youtube.com/watch?v=01zAtSYNlvY`
    },
    {
        id: 82,
        content: `YouTube Video Title: Claude Opus 4.6 vs GPT-5.3 Codex: How I shipped 93,000 lines of code in 5 days
Channel: How I AI
Duration: 30 minutes
URL: https://www.youtube.com/watch?v=01zAtSYNlvY&t=247s`
    },
    {
        id: 80,
        content: `Title: Claude Opus 4.6 vs GPT-5.3 Codex: How I shipped 93,000 lines of code in 5 days
Channel: How I AI
Duration: 30 minutes
URL: https://m.youtube.com/watch?v=01zAtSYNlvY&t=247s&pp=ugUHEgVlbi1VUw%3D%3D`
    }
];

testCases.forEach(tc => {
    const result = extractVideoUrl(tc.content);
    console.log(`Entry ${tc.id}: extractVideoUrl = ${result ? `"${result}"` : 'NULL'}`);
});

// Also test: does ReactPlayer accept these URLs?
// ReactPlayer checks if url is truthy. If extractVideoUrl returns a string, it should work.
// The condition in JSX is:
// (extractVideoUrl(entry.processed_content || entry.raw_content) || entry.content_type === 'youtube' || ...)
// So if extractVideoUrl returns a string, condition is truthy.
// But is the player actually rendering? Maybe the issue is CSS (hidden, zero height)?
// Or maybe the entry is in collapsed state (not expanded)?

console.log("\n--- CRITICAL CHECK ---");
console.log("The video player ONLY renders inside the EXPANDED view (expandedEntryId === entry.id).");
console.log("If the entry is NOT clicked/expanded, the player is hidden.");
console.log("The collapsed view (line 198-203) only shows text, no player.");
