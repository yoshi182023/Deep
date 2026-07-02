import time
from models import db, AgentLog

MODEL_COSTS = {
    "llama3.2": {"input": 0.0, "output": 0.0},
    "gpt-4": {"input": 0.00003, "output": 0.00006},
    "gpt-3.5-turbo": {"input": 0.0000015, "output": 0.000002},
    "claude-3-sonnet": {"input": 0.000003, "output": 0.000015},
    "claude-3-haiku": {"input": 0.00000025, "output": 0.00000125},
}


def estimate_tokens(text):
    return len(text) // 4


def calculate_cost(model, input_tokens, output_tokens):
    costs = MODEL_COSTS.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens * costs["input"]) + (output_tokens * costs["output"])


def log_llm_call(agent_name, operation, model, prompt, response_content, latency_ms):
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(response_content)
    total_tokens = input_tokens + output_tokens
    cost_usd = calculate_cost(model, input_tokens, output_tokens)

    try:
        log = AgentLog(
            agent_name=agent_name,
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms
        )
        db.session.add(log)
        db.session.commit()
        return log.to_dict()
    except Exception:
        return {}


class TrackedLLM:
    def __init__(self, llm, agent_name, operation):
        self.llm = llm
        self.agent_name = agent_name
        self.operation = operation
        self.model = getattr(llm, 'model', 'unknown')

    def invoke(self, prompt):
        start_time = time.time()
        response = self.llm.invoke(prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        log_llm_call(
            agent_name=self.agent_name,
            operation=self.operation,
            model=self.model,
            prompt=str(prompt),
            response_content=response.content,
            latency_ms=latency_ms
        )

        return response
