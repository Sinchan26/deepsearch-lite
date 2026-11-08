---
name: frontend-engineering
description: Build the DeepResearch Lite React research workspace using typed SSE events and accessible evidence and critique views.
---

Read phase 004 and shared event contracts before UI work. Use React/TypeScript/Vite, Tailwind, shadcn/ui and Motion for React. Keep transport parsing separate from presentation. Render only validated public events, preserve order and deduplicate event IDs. Show actions, searches, source evidence, draft status, critique, limits and terminal outcomes honestly. Render citations as accessible safe links; sanitize Markdown and disable raw HTML. Support keyboard navigation, reduced motion and readable live announcements. Keep API secrets server-side and run state in memory; no localStorage or IndexedDB. Test disconnect/replay gaps, cancellation and partial answers with Vitest.
