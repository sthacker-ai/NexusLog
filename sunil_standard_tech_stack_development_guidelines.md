# 🧭 Sunil’s Standard Tech Stack & Development Guidelines

*(Version 1.0 — Living Document)*

---

## 1. Purpose of This Document

This document defines my **default, standardized tech stack and engineering principles** for all personal and experimental projects.

**Goals:**
- Avoid analysis paralysis
- Ensure consistency across projects
- Reduce decision-making overhead
- Enable faster “vibe coding” with AI assistance
- Keep everything cost-effective, secure, and maintainable

Unless there is a **strong, explicit reason**, all projects should follow this stack.

---

## 2. High-Level Architecture (Mental Model)

```
[ Browser / Mobile ]
        ↓
[ React + Tailwind (PWA) ]
        ↓
[ Backend APIs (Flask / Serverless) ]
        ↓
[ Database / Analytics / AI APIs ]
```

- Frontend is pure UI
- Backend handles logic, security, API calls
- Secrets are never exposed to frontend
- Analytics & dashboards are separate, specialized tools

---

## 3. Frontend Standards

### 3.1 Framework

**React.js**

**Why:**
- Industry standard
- Massive community
- Long-term stability
- Works well with AI-assisted coding

---

### 3.2 Styling

**Tailwind CSS**

**Why:**
- Utility-first (fast iteration)
- No heavy component lock-in
- Performance-friendly
- Easy to keep UI consistent

**Guideline:**
- Prefer Tailwind utilities
- Avoid large custom CSS files unless necessary

---

### 3.3 Build Tool

**Vite**

**Why:**
- Extremely fast dev server
- Simple configuration
- Excellent React integration

---

### 3.4 Frontend Stack Summary

```
React + Tailwind CSS + Vite
```

---

## 4. Mobile Strategy (Mandatory)

### 4.1 Primary Approach

**Progressive Web App (PWA)**

All web apps must:
- Be mobile-responsive
- Work well on phone browsers
- Support “Add to Home Screen”
- Feel app-like without App Store costs

**Reasons:**
- No Google Play / Apple App Store fees
- One codebase
- Perfect for personal and experimental projects

---

### 4.2 PWA Requirements (Must-Have)

- Responsive layouts (mobile-first thinking)
- Web manifest (`manifest.json`)
- App icons
- Offline-friendly where reasonable
- Touch-friendly UI elements

**Instruction to AI Pair Programmer:**

> This application must be built as a mobile-first Progressive Web App (PWA). All UI and UX decisions should consider mobile usability first.

---

## 5. Backend Standards

### 5.1 Backend Language

**Python**

**Why:**
- Readable
- Strong ecosystem
- Excellent for APIs, data, AI integration

---

### 5.2 Backend Framework

**Flask**

**Role:**
- API routing
- Business logic
- Input validation
- Server-side processing
- Secure communication with databases and AI APIs

**Important:**
- Flask is not hosting
- Flask is application logic

---

### 5.3 Hosting & Deployment

**Vercel (Primary)**  
(Netlify acceptable alternative)

**Guidelines:**
- Use Vercel for frontend hosting
- Use Vercel serverless functions for backend APIs when possible
- No need to manage IIS / Apache / Nginx manually

---

## 6. Database Standards

### 6.1 Primary Database (Structured Data)

**PostgreSQL**

**Use cases:**
- Stock market data
- Time-series data
- Relational data
- Anything with schema, joins, analytics

**Why:**
- Powerful querying
- Reliable
- Industry-proven
- Ideal for large datasets

---

### 6.2 What NOT to Use for Large Structured Data

- Firebase / Firestore
- JSON-tree databases

**Reason:**
- Not suitable for large historical time-series (e.g., 10 years of stock data)

---

## 7. Analytics, BI & Dashboarding

### 7.1 Standard Tool

**Grafana**

This choice is finalized and locked in.

**Why:**
- Excellent for time-series data
- Open-source
- Highly scalable
- Works well with PostgreSQL
- Handles both simple and advanced dashboards

**Usage:**
- Stock market dashboards
- System metrics
- Analytics views
- Read-only or exploratory dashboards

---

## 8. Authentication & User Identity

### 8.1 Supported Authentication Modes (Always Both)

All apps must support both:

1. **Third-party login**
   - Google
   - Apple (optional)
2. **Native login**
   - Email / username
   - Password

**Reason:**
- Do not force users into social login
- Respect privacy preferences

---

### 8.2 Authentication Principles

- Authentication logic lives in backend
- Passwords must be hashed (never stored plain)
- OAuth handled via trusted libraries

---

## 9. API Design Principles

- Frontend never talks directly to third-party APIs
- All external API calls go through backend
- Backend acts as a secure proxy

**Examples:**
- OpenAI / Gemini
- Google APIs
- PDF processing libraries

---

## 10. Security Standards (Mandatory)

### 10.1 Core Rules

- Never expose secrets in frontend
- Never commit secrets to Git
- Use HTTPS always
- Validate and sanitize all inputs

---

### 10.2 Dependency Safety

- Use trusted libraries
- Keep dependencies updated
- Avoid random CDN imports unless necessary

---

### 10.3 Browser-Level Protection

- Use Content Security Policy (CSP)
- Restrict external scripts and resources

---

### 10.4 Logging & Monitoring

- Log backend errors
- Avoid logging sensitive data
- Use logs for debugging, not secrets

---

## 11. Secrets & API Key Management

🚧 **ON HOLD — DECISION PENDING**

**Status:**
- No final decision yet
- Options under consideration:
  - Vercel Environment Variables
  - Cloud secret managers
  - Open-source secret vaults

**Temporary Rule:**
> No secrets are allowed in frontend code or repositories.

---

## 12. AI Usage Guidelines

- AI is a pair programmer, not an architect
- Stack decisions come from this document, not the model
- AI may:
  - Generate code
  - Explain concepts
  - Speed up development
- AI must NOT:
  - Change tech stack
  - Introduce new tools without approval

---

## 13. Default Stack Summary (TL;DR)

```
Frontend:     React + Tailwind + Vite
Backend:      Python + Flask
Hosting:      Vercel
Database:     PostgreSQL
Dashboards:   Grafana
Mobile:       PWA (mandatory)
Auth:         Social + Native
Secrets:      TBD (on hold)
Security:     CSP, HTTPS, backend-only secrets
```

---

## 14. Final Principle

> Consistency beats perfection.

This stack is good enough to build fast, learn deeply, and iterate endlessly.

