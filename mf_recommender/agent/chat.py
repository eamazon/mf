"""Interactive chat agent powered by Claude with tool use for mutual fund analysis."""

import json
import os

from anthropic import Anthropic

from .tools import TOOLS
from .executor import execute_tool

SYSTEM_PROMPT = """\
You are an expert Indian mutual fund advisor assistant. You help users discover, \
analyze, and compare mutual funds using real data from public APIs.

YOUR CAPABILITIES (via tools):
- Search and analyze any Indian mutual fund by name or scheme code
- Recommend top funds by category (Large Cap, Mid Cap, Small Cap, Flexi Cap, etc.)
- Compare multiple funds side by side
- Build diversified portfolios based on risk tolerance and goals
- Calculate SIP amounts needed for financial goals
- Assess an investor's risk profile
- Explain any financial metric in plain English

IMPORTANT GUIDELINES:
1. ALWAYS use tools to fetch real data before making recommendations. Never guess fund \
performance numbers.
2. Explain metrics in simple terms. The user is not a financial professional.
3. When recommending funds, explain WHY each fund scored well or poorly.
4. For portfolio advice, always ask about risk tolerance, time horizon, and monthly budget \
if the user hasn't provided them.
5. Always include the disclaimer that this is for educational purposes, not financial advice.
6. Use Indian financial context: rupees, lakhs, crores, SEBI categories, Indian tax rules \
(80C for ELSS, LTCG, STCG).
7. When comparing funds, highlight trade-offs (e.g., higher returns vs higher volatility).
8. If the user seems new to investing, proactively explain what metrics mean.

SCORING GUIDE:
- 80+ Excellent | 65-80 Very Good | 50-65 Good | 35-50 Average | <35 Below Average
- Sharpe >1.5 great, >1 good, <0.5 poor
- Consistency >80% is strong
- Always recommend Direct Growth plans over Regular plans.

FORMAT:
- Use clear sections and bullet points
- Bold key numbers and fund names
- Include the composite score and 2-3 most important metrics for each fund
- For portfolios, show a clear allocation table
"""

MAX_TURNS = 25  # Safety limit for agent loop per user message


def create_agent(api_key: str | None = None) -> "MFAgent":
    """Create a new chat agent instance."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Either:\n"
            "  1. Export it: export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  2. Pass it:  mf chat --api-key sk-ant-..."
        )
    return MFAgent(key)


class MFAgent:
    """Conversational mutual fund advisor backed by Claude + data tools."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.messages: list[dict] = []
        self.model = "claude-sonnet-4-5-20250929"

    def chat(self, user_message: str) -> str:
        """Send a message and get back the agent's response.

        The agent may call tools (data lookups, calculations) behind the scenes
        before responding. This method handles the full agentic loop.
        """
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(MAX_TURNS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.messages,
            )

            # Collect the assistant's content blocks
            self.messages.append({"role": "assistant", "content": response.content})

            # If the model wants to use tools, execute them and feed results back
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                self.messages.append({"role": "user", "content": tool_results})
                continue

            # Model is done (end_turn) - extract text response
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            return "\n".join(text_parts)

        return "[Agent hit the maximum number of tool calls. Please try a simpler query.]"

    def reset(self):
        """Clear conversation history."""
        self.messages = []
