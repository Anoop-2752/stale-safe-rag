import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag_pipeline import ask

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ask.py \"your question here\"")
        return

    query = " ".join(sys.argv[1:])
    result = ask(query)

    print(f"\nQ: {query}")
    print(f"A: {result['answer']}")
    print(f"\n[source: {result['source']}]", end="")
    if result.get("stale"):
        print(" ⚠️  WARNING: this answer may be outdated", end="")
    print()

if __name__ == "__main__":
    main()