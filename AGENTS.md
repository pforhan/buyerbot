# Agent Rules and Instructions for BuyerBot

As an AI coding agent working on this project, you must adhere to these specific guidelines to ensure code quality, consistency, and safe operation.

## Core Architectural Principles

- **Extensibility First**: All LLM-related logic must reside in the `llm/` directory and inherit from `llm.base.LLMProvider`. Never hardcode provider-specific logic in `app.py` or `processor.py`.
- **Database Integrity**: Use `sqlmodel` for all database interactions. Ensure that `slack_ts` remains the unique identifier for posts to prevent duplicate indexing.
- **Statelessness**: The Slack app uses Socket Mode and is designed to be largely stateless, relying on the SQLite database (`buyerbot.db`) for persistence.

## Coding Standards

- **Type Hinting**: All new functions and methods should include Python type hints.
- **Async/Await**: While the current implementation is synchronous for simplicity, prefer `httpx` for external API calls to facilitate a future move to an async architecture.
- **Error Handling**: Implement robust error handling, especially around Slack API calls and LLM provider interactions. Always provide user-friendly error messages in Slack when a command fails.

## Slack Integration Guidelines

- **Block Kit**: Use Slack's [Block Kit](https://api.slack.com/block-kit) for rich formatting in responses. Avoid sending large chunks of unformatted text.
- **Ack First**: Always call `ack()` immediately in Slack command handlers to prevent timeout errors.
- **Rate Limiting**: Be mindful of Slack's API rate limits, especially in `processor.py` when fetching history and thread replies.

## LLM Interaction Rules

- **JSON Enforcement**: When prompting LLMs for structured data, explicitly request JSON format and provide a clear schema. Always wrap LLM parsing in `try/except` blocks to handle malformed JSON.
- **Context Management**: Keep LLM prompts concise. When analyzing Slack posts, only send the necessary message text and thread content.

## Testing and Validation

- **Mock Provider**: Before testing with a live LLM (Ollama/Claude/etc.), ensure your changes work with the `MockProvider`.
- **Database Migrations**: If you change the `SlackPost` model in `db.py`, ensure you provide a plan for migrating the local `buyerbot.db`.

## Safety and Security

- **Secrets**: Never hardcode Slack tokens or API keys. Always use `os.environ` and document new variables in `.env.example`.
- **Data Privacy**: Do not log full Slack message contents to the console or files, as they may contain sensitive user information.
