"""CLI interface for Grafana AI Agent."""

import json
import os
import sys
import click
from typing import Optional
from .llm_client import get_llm_client
from .grafana_client import GrafanaClient
from .chat_interface import ChatInterface
from .dashboard_generator import DashboardGenerator


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Grafana AI Agent - Create and summarize Grafana dashboards using LLMs."""
    pass


@cli.command()
@click.option('--provider', default='openai', type=click.Choice(['openai', 'anthropic']), 
              help='LLM provider to use')
@click.option('--model', help='Model name to use (overrides default)')
@click.option('--api-key', help='API key for LLM provider')
@click.option('--grafana-url', envvar='GRAFANA_URL', help='Grafana base URL')
@click.option('--grafana-api-key', envvar='GRAFANA_API_KEY', help='Grafana API key')
@click.option('--grafana-user', envvar='GRAFANA_USER', help='Grafana username')
@click.option('--grafana-password', envvar='GRAFANA_PASSWORD', help='Grafana password')
def chat(provider, model, api_key, grafana_url, grafana_api_key, grafana_user, grafana_password):
    """Start an interactive conversational chat session."""
    click.echo("🤖 Grafana AI Agent - Conversational Mode")
    click.echo("Type 'exit' or 'quit' to end the session\n")
    
    # Initialize LLM client
    try:
        llm_kwargs = {}
        if model:
            llm_kwargs['model'] = model
        if api_key:
            llm_kwargs['api_key'] = api_key
        
        llm_client = get_llm_client(provider, **llm_kwargs)
    except Exception as e:
        click.echo(f"❌ Error initializing LLM client: {e}", err=True)
        sys.exit(1)
    
    # Initialize Grafana client if credentials provided
    grafana_client = None
    if grafana_url:
        try:
            if grafana_api_key:
                grafana_client = GrafanaClient(grafana_url, api_key=grafana_api_key)
            elif grafana_user and grafana_password:
                grafana_client = GrafanaClient(grafana_url, username=grafana_user, password=grafana_password)
            else:
                click.echo("⚠️  Grafana URL provided but no credentials. Dashboard creation will be local only.", err=True)
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not initialize Grafana client: {e}", err=True)
    
    # Initialize chat interface
    chat_interface = ChatInterface(llm_client, grafana_client)
    
    # Interactive loop
    while True:
        try:
            user_input = click.prompt("\n💬 You", default="", show_default=False)
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                click.echo("\n👋 Goodbye!")
                break
            
            if not user_input.strip():
                continue
            
            # Check for special commands
            if user_input.startswith('/create'):
                # Extract description
                description = user_input[7:].strip()
                if not description:
                    click.echo("❌ Please provide a description. Usage: /create <description>")
                    continue
                
                click.echo("\n🔄 Generating dashboard...")
                try:
                    dashboard = chat_interface.create_dashboard(description)
                    click.echo("\n✅ Dashboard generated successfully!")
                    
                    # Ask if user wants to save to Grafana
                    if grafana_client:
                        if click.confirm("\n📤 Upload to Grafana?"):
                            try:
                                result = grafana_client.create_dashboard(dashboard.get("dashboard", dashboard))
                                click.echo(f"✅ Dashboard uploaded! URL: {result.get('url', 'N/A')}")
                            except Exception as e:
                                click.echo(f"❌ Error uploading to Grafana: {e}", err=True)
                    
                    # Ask if user wants to save to file
                    if click.confirm("\n💾 Save to file?"):
                        filename = click.prompt("Filename", default="dashboard.json")
                        with open(filename, 'w') as f:
                            json.dump(dashboard, f, indent=2)
                        click.echo(f"✅ Saved to {filename}")
                except Exception as e:
                    click.echo(f"❌ Error creating dashboard: {e}", err=True)
            
            elif user_input.startswith('/summarize'):
                # Extract file path or UID
                arg = user_input[10:].strip()
                if not arg:
                    click.echo("❌ Please provide a file path or dashboard UID. Usage: /summarize <file_or_uid>")
                    continue
                
                click.echo("\n🔄 Analyzing dashboard...")
                try:
                    # Try as file first
                    if os.path.exists(arg):
                        with open(arg, 'r') as f:
                            dashboard_json = json.load(f)
                    # Try as Grafana UID
                    elif grafana_client:
                        try:
                            result = grafana_client.get_dashboard(arg)
                            dashboard_json = result.get('dashboard', result)
                        except:
                            click.echo(f"❌ Could not find file or dashboard UID: {arg}")
                            continue
                    else:
                        click.echo(f"❌ File not found and no Grafana connection: {arg}")
                        continue
                    
                    summary = chat_interface.summarize_dashboard(dashboard_json)
                    click.echo(f"\n📊 Dashboard Summary:\n\n{summary}")
                except Exception as e:
                    click.echo(f"❌ Error summarizing dashboard: {e}", err=True)
            
            elif user_input.startswith('/reset'):
                chat_interface.reset_conversation()
                click.echo("🔄 Conversation history reset")
            
            elif user_input.startswith('/help'):
                click.echo("""
📖 Available Commands:
  /create <description>    - Create a new dashboard
  /summarize <file_or_uid> - Summarize a dashboard
  /reset                  - Reset conversation history
  /help                   - Show this help message
  exit/quit/q             - Exit the chat session

You can also just chat naturally about dashboards!
                """)
            
            else:
                # Regular chat
                response = chat_interface.chat(user_input)
                click.echo(f"\n🤖 Assistant: {response}")
        
        except KeyboardInterrupt:
            click.echo("\n\n👋 Goodbye!")
            break
        except EOFError:
            click.echo("\n\n👋 Goodbye!")
            break
        except Exception as e:
            click.echo(f"\n❌ Error: {e}", err=True)


@cli.command()
@click.argument('description')
@click.option('--title', help='Dashboard title')
@click.option('--output', '-o', help='Output file path')
@click.option('--provider', default='openai', type=click.Choice(['openai', 'anthropic']), 
              help='LLM provider to use')
@click.option('--model', help='Model name to use')
@click.option('--api-key', help='API key for LLM provider')
@click.option('--grafana-url', envvar='GRAFANA_URL', help='Grafana base URL')
@click.option('--grafana-api-key', envvar='GRAFANA_API_KEY', help='Grafana API key')
@click.option('--upload', is_flag=True, help='Upload to Grafana after creation')
def create(description, title, output, provider, model, api_key, grafana_url, grafana_api_key, upload):
    """Create a Grafana dashboard from a description."""
    click.echo("🔄 Generating dashboard...")
    
    # Initialize LLM client
    try:
        llm_kwargs = {}
        if model:
            llm_kwargs['model'] = model
        if api_key:
            llm_kwargs['api_key'] = api_key
        
        llm_client = get_llm_client(provider, **llm_kwargs)
    except Exception as e:
        click.echo(f"❌ Error initializing LLM client: {e}", err=True)
        sys.exit(1)
    
    # Generate dashboard
    generator = DashboardGenerator(llm_client)
    try:
        dashboard = generator.create_dashboard(description, title)
    except Exception as e:
        click.echo(f"❌ Error creating dashboard: {e}", err=True)
        sys.exit(1)
    
    # Save to file
    if output:
        with open(output, 'w') as f:
            json.dump(dashboard, f, indent=2)
        click.echo(f"✅ Dashboard saved to {output}")
    else:
        click.echo(json.dumps(dashboard, indent=2))
    
    # Upload to Grafana if requested
    if upload:
        if not grafana_url or not grafana_api_key:
            click.echo("❌ Grafana URL and API key required for upload", err=True)
            sys.exit(1)
        
        try:
            grafana_client = GrafanaClient(grafana_url, api_key=grafana_api_key)
            result = grafana_client.create_dashboard(dashboard.get("dashboard", dashboard))
            click.echo(f"✅ Dashboard uploaded! URL: {result.get('url', 'N/A')}")
        except Exception as e:
            click.echo(f"❌ Error uploading to Grafana: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--provider', default='openai', type=click.Choice(['openai', 'anthropic']), 
              help='LLM provider to use')
@click.option('--model', help='Model name to use')
@click.option('--api-key', help='API key for LLM provider')
def summarize(input_file, provider, model, api_key):
    """Summarize a Grafana dashboard from a JSON file."""
    click.echo("🔄 Analyzing dashboard...")
    
    # Load dashboard
    try:
        with open(input_file, 'r') as f:
            dashboard_json = json.load(f)
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}", err=True)
        sys.exit(1)
    
    # Initialize LLM client
    try:
        llm_kwargs = {}
        if model:
            llm_kwargs['model'] = model
        if api_key:
            llm_kwargs['api_key'] = api_key
        
        llm_client = get_llm_client(provider, **llm_kwargs)
    except Exception as e:
        click.echo(f"❌ Error initializing LLM client: {e}", err=True)
        sys.exit(1)
    
    # Generate summary
    generator = DashboardGenerator(llm_client)
    try:
        summary = generator.summarize_dashboard(dashboard_json)
        click.echo(f"\n📊 Dashboard Summary:\n\n{summary}")
    except Exception as e:
        click.echo(f"❌ Error summarizing dashboard: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

