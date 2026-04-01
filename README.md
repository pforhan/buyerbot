# BuyerBot

**BuyerBot** is a Slack app designed to help users navigate and summarize busy buy/sell channels. It uses an LLM-powered backend to parse user requests and analyze historical messages, building an indexed database of items, prices, and availability.

## Goals

- **Summarization**: Quickly understand what's available in a channel without scrolling through hundreds of messages.
- **Intelligent Search**: Use natural language to find specific items (e.g., "/buyerbot what macbooks are available?").
- **Multi-Product Support**: A single Slack post can contain multiple items, and BuyerBot will index them individually.
- **Seller Tracking**: Automatically identifies the Slack user who posted an item, allowing you to click their name to start a DM.
- **Status Tracking**: Automatically detect if an item is "Sold" by analyzing thread replies and emojis.
- **Extensibility**: Easily switch between different LLM providers (Mock, Ollama, Claude, Gemini, etc.).

## The Plan

1.  **Request Parsing**: Use an LLM to extract intent and product entities from user commands.
2.  **Message Analysis**: Use an LLM to analyze historical posts and their threads to extract:
    - Multiple Product Names (if applicable)
    - Prices
    - Features
    - Availability Status (Available, Sold, Pending)
3.  **Local Indexing**: Store extracted data in a local SQLite database (using `Post` and `Item` models) for fast searching.
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
  - **Tip**: For faster processing on local hardware, try smaller models like `nemotron-mini` or `llama3`.

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

1.  **Invite the bot**: Invite @BuyerBot to your buy/sell channel.
2.  **Sync History**: Run `/buyerbot sync` (or `/buyerbot-sync`) to index existing channel messages.
3.  **Search**: Use `/buyerbot search <query>` (or just `/buyerbot <query>`) to find items.
4.  **Add Listings**: Use `/buyerbot add <description>` to list an item for sale.
5.  **Seek Items**: Use `/buyerbot seeking <description>` if you are looking for something.
6.  **Manage Dashboard**: Type `/buyerbot` (empty) to open the **Overview Modal** for quick actions.
7.  **Manage Your Items**: Run `/buyerbot list` (or `manage`) to see and edit your active listings.

## Direct Listing & Management

BuyerBot allows users to bypass historical parsing and list items directly. These "Direct Listings" are prioritized in search results and come with built-in management tools.

### Subcommands
- `/buyerbot add Selling my bike for $100`: Immediately creates a structured "Sale" listing.
- `/buyerbot seeking Looking for an IKEA desk`: Creates a "Seeking" (WTB) entry.
- `/buyerbot list`: Shows an ephemeral dashboard of your entries.

### Management Dashboard
From the `/buyerbot list` dashboard, you can:
- **Mark Sold**: Hide the item from search results (for sales).
- **Mark Obsolete**: Mark a seeking request as no longer needed.
- **Edit**: Update the name, price, or description via a Modal.
- **Delete**: Permanently remove the listing.

### Overview Modal
Simply typing `/buyerbot` without any arguments opens a central hub. From here, you can:
- Open the **Add Listing** or **Seeking Item** forms.
- View **My Listings**.
- Trigger a **Sync** of the current channel.

## Testing

This project uses `pytest` for testing.

### Running Tests

It's recommended to run tests from within the project's virtual environment to ensure all dependencies are correctly loaded.

1.  **Activate the Virtual Environment** (if not already):
    ```bash
    source .venv/bin/activate
    ```

2.  **Ensure Test Dependencies are Installed**:
    ```bash
    pip install pytest
    ```

3.  **Run All Tests**:
    ```bash
    pytest
    ```
    *Alternatively, you can run tests without activating the venv by using the venv's python directly:*
    ```bash
    ./.venv/bin/python3 -m pytest
    ```

4.  **Run Specific Tests**:
    ```bash
    pytest tests/test_ollama.py
    ```

### Debugging and Logging in Tests

By default, `pytest` captures all standard output and only shows it on test failure. To see the output of passing tests (including LLM prompts and responses), use the `-s` flag.

You can control the verbosity of the output using the `DEBUG_LEVEL` environment variable:
- `none` (default): No diagnostic output from the application.
- `basic`: Shows high-level status messages.
- `full`: Shows detailed logs, including full LLM interaction prompts and JSON responses.

**Example**:
```bash
# Run tests with full LLM diagnostic output
DEBUG_LEVEL=full pytest -s tests/test_ollama.py
```

**Note**: Some tests (like the Ollama integration tests) require a local Ollama instance running and accessible. You can configure the model and timeout via environment variables in your `.env` file:
- `OLLAMA_MODEL`: The model to use (defaults to `llama3`).
- `OLLAMA_TIMEOUT`: Timeout for Ollama requests (defaults to `60` seconds).
- `DEBUG_LEVEL`: Verbosity for diagnostic output (`none`, `basic`, `full`).

