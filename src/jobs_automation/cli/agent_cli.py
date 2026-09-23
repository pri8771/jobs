import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Jobs Automation Agent CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("task_type", help="Type of task to start")
    
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("task_id", help="Task ID to check status")
    
    args = parser.parse_args()
    
    if args.command == "start":
        print(f"Starting task {args.task_type}")
    elif args.command == "status":
        print(f"Status for task {args.task_id}: RUNNING")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
