# KreeperAI

KreeperAI is an AI-powered assistant that helps developers add **specific features** to existing codebases — without rebuilding the whole application.

Instead of asking an AI to “generate an entire app”, KreeperAI focuses on **incremental development**: it understands your project, then guides you with code changes that fit naturally into it.

---

## 🚀 What problem does it solve?

Most AI tools struggle with real-world codebases:

- They don’t fully understand project structure
- They overwrite files instead of modifying them safely
- They generate code that doesn’t match the project style
- Developers waste time integrating and fixing AI output

KreeperAI is built to work **inside existing projects**, not replace them.

---

## ✨ What KreeperAI does

- 🔎 Analyzes your repository (GitHub or local project)
- 🧠 Understands architecture, dependencies, and patterns
- 📝 Accepts natural-language feature requests (e.g.,  
  _“Add JWT authentication and protect the dashboard API”_)
- 🛠 Generates **targeted diffs and code suggestions**
- 📌 Explains where changes go — and why
- ⚠ Avoids overwriting working code

KreeperAI acts like a smart collaborator sitting in your IDE.

---

## 🎯 Why it’s useful

KreeperAI helps you:

- build faster without rewriting everything
- safely introduce new features
- reduce bugs caused by copy-paste AI code
- learn best practices from structured explanations
- integrate AI output confidently

It’s especially powerful for:

- growing startups
- hackathon teams
- junior developers
- solo builders maintaining large projects
- product teams shipping frequent updates

---

## 🌟 The vision

KreeperAI bridges the gap between:

> **“AI generated some code”**  
> and  
> **“this integrates cleanly into my real project.”**

By focusing on _feature-level intelligence_, it supports modern, iterative development instead of one-shot code generation.

---

## 📌 Status: Technical Preview

KreeperAI is currently in active development.

### ✅ Implemented Features

- **Multi-Agent Orchestration**: Specialized agents for Feature Generation, Code Explanation, and Project Management.
- **Context-Aware Chat**: Agents have full awareness of the repository structure and file contents.
- **Real-time Streaming**: SSE-based chat interface with "Thinking" process visibility.
- **Session Management**: Persistent chat sessions with history tracking.
- **Repository Analysis**: Smart file tree exploration and indexing.

### 🎉 Phase 1 Successfully Completed — January 18, 2026

---

## 🗺️ Roadmap: Phase 2 - January 19, 2026

### Core Enhancements

### 1. Chat & Visuals

- [ ] Enhanced chat styling (Typography, Avatars)
- [ ] Rich message formatting (Markdown, Code Blocks)
- [ ] Contextual user message styling

### 2. File Operations

- [ ] Backend support for creating and editing files
- [ ] Frontend UI for accepting/rejecting proposed changes
- [ ] Direct file manipulation by agents

### 3. Diff Viewer

- [ ] GitHub-style diff viewer for proposed code changes
- [ ] Line-by-line comparison (Old vs New)

### 4. Advanced Tooling

- [ ] **Testing Agent**: Dedicated agent for running and verifying tests
- [ ] **Active Features**: Sidebar management for ongoing tasks
- [ ] **User API Key**: Secure, per-session API key management UI
- [ ] **Token Management & Rate Limits**: Actual LLM token counts and usage tracking, per-user rate limiting

### MCP for Playwright
