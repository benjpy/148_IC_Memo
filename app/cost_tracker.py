import time

class CostTracker:
    # Gemini 2.5 Flash Pricing (per 1M tokens)
    INPUT_PRICE_PER_1M = 0.30
    OUTPUT_PRICE_PER_1M = 2.50

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = 0
        self.end_time = 0

    def start_timer(self):
        self.start_time = time.time()

    def stop_timer(self):
        self.end_time = time.time()

    def add_tokens(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def calculate_cost(self) -> float:
        input_cost = (self.total_input_tokens / 1_000_000) * self.INPUT_PRICE_PER_1M
        output_cost = (self.total_output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_1M
        return input_cost + output_cost

    def get_duration(self) -> float:
        if self.end_time == 0:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def get_summary(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.calculate_cost(),
            "total_runtime_seconds": self.get_duration()
        }
