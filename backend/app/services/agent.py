import logging
import re

from backend.app.services.llm import run_llm
from backend.app.services.tools import Tool

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are an AI agent that solves tasks step by step using tools.

Available tools:
{tool_descriptions}

You MUST respond in exactly this format, one step at a time:

Thought: <your reasoning about what to do next>
Action: <the tool name to use>
Action Input: <the input to give the tool>

When you have enough information to answer the task, respond instead with:

Thought: <your reasoning>
Final Answer: <the final answer to the task>

Do not do more than one Thought/Action per response. Wait for the Observation before continuing.

If a previous Observation already answers part of the task, do not repeat the same Action with the same or similar Action Input. Move on to whatever information is still missing.

Task: {task}

{history}"""


def _build_tool_descriptions(tools: dict[str, Tool]) -> str:
    return "\n".join(f"- {tool.name}: {tool.description}" for tool in tools.values())


def _parse_response(text: str):
    thought_match = re.search(r"Thought:\s*(.+?)(?:\n(?:Action|Final Answer):|\Z)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else "(no thought given)"

    final_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if final_match:
        return {"type": "final", "thought": thought, "answer": final_match.group(1).strip()}

    action_match = re.search(r"Action:\s*(.+)", text)
    input_match = re.search(r"Action Input:\s*(.+)", text)

    if action_match and input_match:
        return {
            "type": "action",
            "thought": thought,
            "tool": action_match.group(1).strip(),
            "input": input_match.group(1).strip(),
        }

    return {"type": "unparseable", "raw": text}


async def run_agent(
    task: str,
    tools: dict[str, Tool],
    model: str = "qwen2.5-coder:7b",
    max_iterations: int = 5,
    on_step=None,
) -> dict:
    tool_descriptions = _build_tool_descriptions(tools)
    history = ""
    steps = []

    for step_number in range(1, max_iterations + 1):
        prompt = AGENT_SYSTEM_PROMPT.format(
            tool_descriptions=tool_descriptions,
            task=task,
            history=history,
        )

        llm_result = await run_llm(prompt=prompt, model=model)
        parsed = _parse_response(llm_result.response)

        if on_step:
            await on_step("llm_call", model, prompt, llm_result.response, llm_result.latency_ms)

        if parsed["type"] == "final":
            steps.append({"step": step_number, "type": "final_answer", "content": parsed["answer"]})
            return {"answer": parsed["answer"], "steps": steps}

        if parsed["type"] == "action":
            tool_name = parsed["tool"]
            tool_input = parsed["input"]

            if tool_name not in tools:
                observation = f"Error: unknown tool '{tool_name}'. Available tools: {list(tools.keys())}"
            else:
                observation = await tools[tool_name].run(tool_input)

            if on_step:
                await on_step("tool_call", tool_name, tool_input, observation, None)

            steps.append({
                "step": step_number,
                "type": "action",
                "tool": tool_name,
                "input": tool_input,
                "observation": observation,
            })

            history += (
                f"\nThought: {parsed['thought']}\n"
                f"Action: {tool_name}\n"
                f"Action Input: {tool_input}\n"
                f"Observation: {observation}\n"
            )
            continue

        logger.warning("Agent produced unparseable response: %s", parsed["raw"])
        steps.append({"step": step_number, "type": "unparseable", "content": parsed["raw"]})
        return {
            "answer": "The agent's response could not be parsed. Stopping.",
            "steps": steps,
        }

    steps.append({"step": max_iterations, "type": "max_iterations_reached"})
    return {
        "answer": "The agent could not finish within the allowed number of steps.",
        "steps": steps,
    }