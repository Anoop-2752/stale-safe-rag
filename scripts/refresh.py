import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.invalidate import run_invalidation

def main():
    result = run_invalidation()

    print(f"Changed chunks: {len(result['changed_chunks'])}")
    for cid in result['changed_chunks']:
        print(f"  - {cid}")

    print(f"\nStale answers: {result['stale_answer_count']}")
    for a in result['stale_answers']:
        print(f"  - \"{a['query_text']}\"")

    if result['stale_answer_count'] == 0:
        print("\nNo cached answers affected. All good.")
    else:
        print("\nThese answers will regenerate next time they're asked.")

if __name__ == "__main__":
    main()