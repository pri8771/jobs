import argparse
import sys
import os
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from jobs_automation.agents.registry import build_parent_graph

def main():
    parser = argparse.ArgumentParser(description="Jobs Automation Agent CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("agent", choices=["market_scout", "opportunity_matcher"], help="Agent to start")
    start_parser.add_argument("query", help="Query to run")
    start_parser.add_argument("--api-key", help="Gemini API Key", default=os.environ.get("GEMINI_API_KEY"))
    
    args = parser.parse_args()
    
    if args.command == "start":
        if not args.api_key:
            print("Error: GEMINI_API_KEY environment variable or --api-key argument is required.")
            sys.exit(1)
            
        print(f"Initializing Gemini model...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=args.api_key,
            temperature=0
        )
        
        print(f"Building graph and routing to {args.agent}...")
        graph = build_parent_graph(llm)
        
        initial_state = {
            "messages": [HumanMessage(content=args.query)],
            "current_agent": args.agent
        }
        
        print(f"Executing...\n")
        result = graph.invoke(initial_state)
        
        print("--- Execution Complete ---")
        for msg in result["messages"]:
            msg_type = msg.type.upper()
            content = msg.content
            if msg_type == "TOOL":
                print(f"[{msg_type}]: (Tool ID: {msg.tool_call_id}) {content}")
            elif msg_type == "AI" and getattr(msg, "tool_calls", []):
                for tc in msg.tool_calls:
                    print(f"[AI TOOL CALL]: {tc['name']}({tc['args']})")
                if content:
                    print(f"[{msg_type}]: {content}")
            else:
                print(f"[{msg_type}]: {content}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
