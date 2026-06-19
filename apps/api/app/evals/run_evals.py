from app.evals.evaluator import run_all_evals


def main() -> None:
    results = run_all_evals()
    metrics = results["metrics"]
    print(f"Total cases: {results['total_cases']}")
    print(f"Passed cases: {results['passed_cases']}")
    print(f"Pass rate: {results['pass_rate']:.2%}")
    print(f"Intent accuracy: {metrics['intent_correct']:.2%}")
    print(f"RAG accuracy: {metrics['rag_usage_correct']:.2%}")
    print(f"Lead extraction accuracy: {metrics['lead_extraction_correct']:.2%}")
    print(f"Approval accuracy: {metrics['approval_correct']:.2%}")
    print(f"Tool-call accuracy: {metrics['tool_call_correct']:.2%}")
    print(f"Average latency: {metrics['average_latency_ms']}ms")
    print(f"Estimated cost: {metrics['estimated_cost']}")
    print("Wrote eval_results/latest_eval_results.json")


if __name__ == "__main__":
    main()
