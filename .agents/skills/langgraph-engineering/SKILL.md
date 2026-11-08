---
name: langgraph-engineering
description: Design or implement DeepResearch Lite graph state, transitions, cancellation and bounded research or critique loops.
---

Read the active phase and specs/architecture.md. Keep graph nodes dependent on typed service ports, not provider SDK objects or HTTP routes. Explicitly enumerate terminal transitions and finite loop counters. Reserve budget before every attempt; retries and critique-driven research share the same ledger. Use in-memory state without disk checkpoints. Cancellation and deadline checks precede node work and retries. Test transitions using fake ports and clocks, including malformed output, exhaustion and cancellation. Emit only allowlisted public summaries; never model reasoning.
