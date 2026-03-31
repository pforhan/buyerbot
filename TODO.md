# BuyerBot TODO List

This document tracks planned features, improvements, and technical debt for the BuyerBot project.

## High Priority
- [ ] **Real-time Sync**: Implement an event listener for `message.channels` to automatically index new posts as they arrive.
- [ ] **Error Handling & Robustness**: Add more comprehensive `try/except` blocks around LLM parsing, especially for non-standard JSON responses.
- [x] **Multi-Product Support**: A single Slack post can contain multiple items, and BuyerBot will index them individually.
- [x] **Seller Tracking**: Automatically identifies the Slack user who posted an item.
- [ ] **Sold Status Detection**: Improve the logic for detecting "Sold" status by specifically looking for common emojis (e.g., :white_check_mark:, :x:) and key phrases in thread replies.

## LLM Providers
- [ ] **Claude (Anthropic)**: Add an `AnthropicProvider` using the `anthropic` Python SDK.
- [ ] **Gemini (Google)**: Add a `GeminiProvider` using the `google-generativeai` SDK.
- [ ] **OpenAI**: Add an `OpenAIProvider`.
- [ ] **Provider-Specific Prompts**: Optimize system prompts for each provider to improve extraction accuracy.

## Architecture & Performance
- [ ] **Async Migration**: Transition from synchronous Bolt to `AsyncApp` and use `async/await` for all I/O operations (Slack API, LLM calls, DB).
- [ ] **Database Migrations**: Integrate `Alembic` to handle future changes to the `sqlmodel` schema.
- [ ] **Vector Search**: Explore using a vector store (e.g., ChromaDB or FAISS) alongside SQLite for better semantic search capabilities.

## User Experience (Slack)
- [ ] **Interactive Summaries**: Allow users to click "Details" on a search result to see the full thread or original message link.
- [ ] **Channel Selection**: Allow `/buyerbot-sync` to take a channel ID or name as an argument.
- [ ] **Pagination**: Handle search results that exceed Slack's block limit by adding pagination buttons.
- [ ] **Better Formatting**: Enhance the Block Kit UI with images (if available in the post) and better visual hierarchy.

## Developer Experience
- [ ] **CLI Tooling**: Add a local CLI script to test LLM extraction against sample message strings without needing Slack.
- [ ] **Test Suite**: Implement `pytest` for unit testing the LLM providers and database logic.
- [x] **Tiered Debug Logging**: Implement a `DEBUG_LEVEL` (none, basic, full) to output activity and LLM interactions to stdout.
- [ ] **Logging**: Implement a proper logging configuration (using the `logging` module) instead of `print` statements.
