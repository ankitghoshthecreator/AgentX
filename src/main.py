import sys
import argparse
import logging
import time

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def query_command(query: str):
    logger = logging.getLogger(__name__)
    logger.info(f"Starting query processing for: {query}")
    
    from src.agent.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()
    orchestrator.process_query(query)

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Agent-as-Database CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Run a natural language query")
    query_parser.add_argument("text", type=str, help="The query text")
    
    # CLI command
    cli_parser = subparsers.add_parser("cli", help="Start interactive CLI")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start the FastAPI server")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    
    args = parser.parse_args()
    
    if args.command == "query":
        query_command(args.text)
    elif args.command == "api":
        from src.api.server import start_server
        start_server(port=args.port)
    elif args.command == "cli":
        print("Agent-as-Database Interactive CLI")
        print("Type 'exit' or 'quit' to stop.")
        while True:
            try:
                user_input = input("\n> ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                if user_input.strip():
                    query_command(user_input)
            except KeyboardInterrupt:
                break
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
