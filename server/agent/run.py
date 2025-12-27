#!/usr/bin/env python3

import sys
from agent import build_agent

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py \"<your question about music.>\"")
        return
    query = sys.argv[1]
    agent = build_agent(verbose=2)
    print("Query:", query)
    result = agent.run(query)
    print("\n=== Final Answer ===\n", result)

if __name__ == "__main__":
    main()
