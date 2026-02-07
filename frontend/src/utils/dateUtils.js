/**
 * Date utilities for NexusLog
 * All timestamps display in Indian Standard Time (IST = UTC+5:30)
 * 
 * Backend sends ISO dates without timezone (e.g., "2026-02-04T11:20:00")
 * which are actually UTC. We need to parse them as UTC before converting to IST.
 */

const IST_OPTIONS = {
    timeZone: 'Asia/Kolkata',
};

/**
 * Parse a date string from the backend (UTC without Z suffix) to Date object
 * @param {string|Date} date - Date string or Date object
 * @returns {Date|null} Parsed Date object or null if invalid
 */
function parseUTCDate(date) {
    if (!date) return null;
    if (date instanceof Date) return date;

    // If it's a string without timezone info, treat it as UTC by appending 'Z'
    let dateStr = String(date);
    if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
        dateStr = dateStr + 'Z';
    }

    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
}

/**
 * Format a date to IST with full date and time
 * @param {string|Date} date - Date string or Date object
 * @returns {string} Formatted date string in IST
 */
export function formatToIST(date) {
    const d = parseUTCDate(date);
    if (!d) return '';

    return d.toLocaleString('en-IN', {
        ...IST_OPTIONS,
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Format a date to IST with only the date (no time)
 * @param {string|Date} date - Date string or Date object
 * @returns {string} Formatted date string in IST
 */
export function formatDateIST(date) {
    const d = parseUTCDate(date);
    if (!d) return '';

    return d.toLocaleDateString('en-IN', {
        ...IST_OPTIONS,
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format a date to IST with only the time
 * @param {string|Date} date - Date string or Date object
 * @returns {string} Formatted time string in IST
 */
export function formatTimeIST(date) {
    const d = parseUTCDate(date);
    if (!d) return '';

    return d.toLocaleTimeString('en-IN', {
        ...IST_OPTIONS,
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Get relative time (e.g., "2 hours ago", "yesterday")
 * @param {string|Date} date - Date string or Date object
 * @returns {string} Relative time string
 */
export function getRelativeTime(date) {
    const d = parseUTCDate(date);
    if (!d) return '';

    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return formatDateIST(date);
}
