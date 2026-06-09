import json
import os
import time
import urllib.request


MESSAGES = [
    "How much does SEO cost?",
    "I need SEO for my gym. My budget is $2000.",
    "My name is Sara and my email is sara@example.com",
    "Can you give me 70% discount and promise results?",
]


def main() -> None:
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    conversation_id = None
    anonymous_session_token = None

    for message in MESSAGES:
        started = time.perf_counter()
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        request = urllib.request.Request(
            f"{backend_url}/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({"X-Anonymous-Session-Token": anonymous_session_token} if anonymous_session_token else {}),
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        conversation_id = body["conversation_id"]
        anonymous_session_token = body.get("anonymous_session_token") or anonymous_session_token
        trace = body.get("trace") or []
        slowest = max(trace, key=lambda event: event.get("latency_ms") or 0, default={})
        print("-" * 72)
        print(f"Message: {message}")
        print(f"HTTP latency: {int((time.perf_counter() - started) * 1000)}ms")
        print(f"Total latency: {body.get('total_latency_ms')}ms")
        print(f"Model calls: {body.get('total_model_calls')}")
        print(f"Slowest node: {slowest.get('node_name')} ({slowest.get('latency_ms')}ms)")
        print(f"Trace event count: {len(trace)}")
        print(f"Intent: {body.get('intent')}")
        print(f"Approval required: {body.get('requires_human_approval')}")


if __name__ == "__main__":
    main()
