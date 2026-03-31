# BuyerBot

**BuyerBot** is a Slack app designed to help users navigate and summarize busy buy/sell channels. It uses an LLM-powered backend to parse user requests and analyze historical messages, building an indexed database of items, prices, and availability.

## Goals

- **Summarization**: Quickly understand what's available in a channel without scrolling through hundreds of messages.
- **Intelligent Search**: Use natural language to find specific items (e.g., "/buyerbot what macbooks are available?").
- **Status Tracking**: Automatically detect if an item is "Sold" by analyzing thread replies and emojis.
- **Extensibility**: Easily switch between different LLM providers (Mock, Ollama, Claude, Gemini, etc.).

## The Plan

1.  **Request Parsing**: Use an LLM to extract intent and product entities from user commands.
2.  **Message Analysis**: Use an LLM to analyze historical posts and their threads to extract:
    - Product Name
    - Price
    - Features
    - Availability Status (Available, Sold, Pending)
3.  **Local Indexing**: Store extracted data in a local SQLite database for fast, efficient searching and to minimize LLM API costs.
4.  **Socket Mode Implementation**: Run locally for development without requiring public endpoints.

## Project Structure

- `app.py`: Main entry point for the Slack app and command handlers.
- `llm/`: Extensible LLM API layer.
    - `base.py`: Base class for providers.
    - `mock.py`: Simple mock implementation for testing.
    - `ollama.py`: Local LLM integration via Ollama.
- `db.py`: SQLite database layer using `sqlmodel`.
- `processor.py`: Logic for syncing channel history and extracting structured data.
- `slack-manifest.yaml`: Slack App Manifest for easy configuration.

## Getting Started

### Prerequisites

- Python 3.10+
- A Slack Workspace (Free tier works great!)
- (Optional) [Ollama](https://ollama.com/) for local LLM support.

### Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd buyerbot
    ```

2.  **Install Dependencies**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure Slack**:
    - Go to the [Slack App Dashboard](https://api.slack.com/apps).
    - Create a new app **From a manifest**.
    - Copy the contents of `slack-manifest.yaml` into the manifest editor.
    - Install the app to your workspace.
    - Generate an **App-Level Token** with `connections:write` scope.
    - Copy the **Bot User OAuth Token** from the "OAuth & Permissions" page.

4.  **Environment Variables**:
    ```bash
    cp .env.example .env
    # Edit .env with your tokens and preferred LLM provider
    ```

5.  **Run the App**:
    ```bash
    python app.py
    ```

## Usage

1.  Invite the bot to your target channel: `/invite @BuyerBot`.
2.  Run `/buyerbot-sync` to index the channel history.
3.  Use `/buyerbot <query>` to search for items.
