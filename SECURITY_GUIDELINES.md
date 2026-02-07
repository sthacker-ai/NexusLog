# Security Guidelines

These guidelines must be followed for all development in this project to ensure security and compliance.

## 1. Server-Side Secrets & Operations
*   **Rule**: All sensitive operations (API calls requiring secret keys, database access, credential handling) must be performed exclusively on the server side.
*   **Implementation**:
    *   Never expose API keys, secrets, or credentials in the frontend code or build bundles.
    *   Use `.env` files for local development and secure environment variables in production.
    *   The frontend should only communicate with our own backend API, which then handles external secure communications if needed.

## 2. Local Dependencies Only (No CDNs)
*   **Rule**: All project dependencies (libraries, packages, APIs) must be sourced from local repositories or managed by the project's native package manager (pip, npm).
*   **Implementation**:
    *   **Strictly Prohibited**: `<script src="https://cdn.jsdelivr.net/...">`, `<link href="https://fonts.googleapis.com/...">`.
    *   Install all libraries via `npm install` or `pip install`.
    *   Host fonts, icons, and scripts locally within the project.

## 3. Zero-Tolerance Content Security Policy (CSP)
*   **Rule**: Always strive for a zero-tolerance CSP. Never use `'unsafe-inline'` or `'unsafe-eval'` unless absolutely necessary and verified.
*   **Implementation**:
    *   Define a strict CSP header in the backend (FastAPI middleware) or HTML meta tag.
    *   **Default Policy Goal**: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self';`
    *   Avoid inline event handlers (e.g., `onclick="..."`) in HTML. Use React/JS event binding.
