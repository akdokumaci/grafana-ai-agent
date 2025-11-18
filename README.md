# Grafana AI Agent

An intelligent agent that uses Large Language Models (LLMs) to create and summarize Grafana dashboards through a conversational interface.

## Features

- 🤖 **Conversational Chat Interface**: Interact naturally with the agent to create and manage dashboards
- 📊 **Dashboard Generation**: Create Grafana dashboards from natural language descriptions
- 📝 **Dashboard Summarization**: Get clear summaries of existing dashboards
- 🔌 **Grafana Integration**: Directly upload dashboards to your Grafana instance
- 🎯 **Multiple LLM Providers**: Support for OpenAI and Anthropic Claude

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd grafana-ai-agent
```

2. Install the package (recommended):
```bash
pip install -e .
```

Or install with development dependencies:
```bash
pip install -e ".[dev]"
```

Alternatively, install dependencies directly:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

The agent can be configured via environment variables or command-line arguments:

### LLM Provider
- `OPENAI_API_KEY`: Your OpenAI API key (for GPT models)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (for Claude models)

### Grafana
- `GRAFANA_URL`: Base URL of your Grafana instance (e.g., `http://localhost:3000`)
- `GRAFANA_API_KEY`: Grafana API key (preferred)
- `GRAFANA_USER` / `GRAFANA_PASSWORD`: Alternative authentication

## Usage

### Conversational Chat Mode

Start an interactive chat session:

```bash
python main.py chat
```

Or with specific options:

```bash
python main.py chat --provider openai --model gpt-4 --grafana-url http://localhost:3000
```

#### Chat Commands

- `/create <description>` - Create a new dashboard
  - Example: `/create a dashboard showing CPU and memory usage over time`
  
- `/summarize <file_or_uid>` - Summarize a dashboard
  - Example: `/summarize dashboard.json` or `/summarize my-dashboard-uid`
  
- `/reset` - Reset conversation history
  
- `/help` - Show help message
  
- `exit` / `quit` / `q` - Exit the chat session

You can also chat naturally about dashboards without using commands!

### Create Dashboard Command

Create a dashboard directly from the command line:

```bash
python main.py create "a dashboard showing server metrics" --title "Server Monitoring" --output dashboard.json
```

Upload directly to Grafana:

```bash
python main.py create "CPU and memory dashboard" --upload --grafana-url http://localhost:3000 --grafana-api-key <key>
```

### Summarize Dashboard Command

Summarize an existing dashboard JSON file:

```bash
python main.py summarize dashboard.json
```

## Examples

### Example 1: Creating a Dashboard via Chat

```bash
$ python main.py chat

💬 You: /create a dashboard for monitoring web server performance with request rate, response time, and error rate

🔄 Generating dashboard...
✅ Dashboard generated successfully!

📤 Upload to Grafana? [y/N]: y
✅ Dashboard uploaded! URL: http://localhost:3000/d/my-dashboard-uid
```

### Example 2: Summarizing a Dashboard

```bash
$ python main.py summarize existing-dashboard.json

📊 Dashboard Summary:

This dashboard monitors application performance metrics. It includes:
- Request rate panel showing requests per second
- Response time graph with p50, p95, and p99 percentiles
- Error rate stat panel
- Uses Prometheus data source
- Time range: last 6 hours
```

### Example 3: Natural Conversation

```bash
$ python main.py chat

💬 You: What are the best practices for creating Grafana dashboards?

🤖 Assistant: Here are some best practices for Grafana dashboards:
1. Use meaningful titles and descriptions
2. Group related panels together
3. Use appropriate visualization types
4. Set reasonable time ranges
5. Add useful annotations
...
```

## Project Structure

```
grafana-ai-agent/
├── grafana_agent/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── chat_interface.py   # Conversational chat interface
│   ├── dashboard_generator.py  # Dashboard generation logic
│   ├── grafana_client.py   # Grafana API client
│   └── llm_client.py       # LLM provider abstractions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_llm_client.py
│   ├── test_grafana_client.py
│   ├── test_dashboard_generator.py
│   ├── test_chat_interface.py
│   └── test_cli.py
├── main.py                 # Entry point
├── pyproject.toml          # Project configuration (PEP 518)
├── setup.py                # Legacy setup file
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── pytest.ini             # Pytest configuration (legacy, pyproject.toml preferred)
├── .env.example           # Example environment variables
└── README.md              # This file
```

## Requirements

- Python 3.8+
- OpenAI API key (for GPT models) or Anthropic API key (for Claude models)
- (Optional) Grafana instance for direct uploads

## LLM Providers

### OpenAI
- Default model: `gpt-4`
- Supported models: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`, etc.
- Set `OPENAI_API_KEY` environment variable

### Anthropic
- Default model: `claude-3-sonnet-20240229`
- Supported models: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- Set `ANTHROPIC_API_KEY` environment variable

## Testing

The project includes a comprehensive test suite using pytest.

### Running Tests

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run all tests:
```bash
pytest
```

3. Run tests with coverage:
```bash
pytest --cov=grafana_agent --cov-report=html
```

4. Run specific test file:
```bash
pytest tests/test_dashboard_generator.py
```

5. Run tests with verbose output:
```bash
pytest -v
```

### Test Coverage

The test suite covers:
- ✅ LLM client implementations (OpenAI and Anthropic)
- ✅ Grafana API client operations
- ✅ Dashboard generation and validation
- ✅ Chat interface functionality
- ✅ CLI commands and error handling

### Writing Tests

Tests use pytest with mocking to avoid external API calls. Key patterns:
- Use fixtures from `conftest.py` for common mocks
- Mock external API calls (LLM and Grafana)
- Test both success and error cases
- Use descriptive test names following `test_<functionality>` pattern

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
