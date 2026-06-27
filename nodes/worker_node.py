"""Agentic worker node: executes ONE action per invocation."""
import logging
from collections import Counter
from typing import Tuple, List, Optional

from langchain_core.messages import ToolMessage, HumanMessage

from chains.worker_chain import TOOL_MAP, worker_llm_with_tools
from prompts.worker_prompt import worker_prompt
from tools.browser_tools import _get_page

logger = logging.getLogger(__name__)

# Maximum number of consecutive identical actions before forcing a stop
MAX_REPEATED_ACTIONS = 3


def _execute_tool_call(tool_call: dict) -> Tuple[ToolMessage, Optional[HumanMessage]]:
    """Execute a single LangChain tool_call dict and return a ToolMessage.

    For screenshot results, returns:
      - A ToolMessage with a short text confirmation
      - A HumanMessage with the image content block (so the vision model can see it)

    For all other tools, returns:
      - A ToolMessage with the string result
      - None (no follow-up message needed)
    """
    name = tool_call["name"]
    args = tool_call["args"]
    call_id = tool_call["id"]

    tool_fn = TOOL_MAP.get(name)
    if tool_fn is None:
        result = f"Error: unknown tool '{name}'"
    else:
        try:
            result = tool_fn.invoke(args)
        except Exception as e:
            result = f"Error executing '{name}': {str(e)}"

    # ----------------------------
    # Handle screenshot results: text ToolMessage + image HumanMessage
    # ----------------------------
    if isinstance(result, dict) and result.get("type") == "image" and result.get("image"):
        image_base64 = result["image"]

        tool_msg = ToolMessage(
            content="Screenshot captured successfully. See the image below.",
            tool_call_id=call_id,
        )

        # Inject image as a HumanMessage — this is the only message role
        # that reliably supports multimodal content in OpenAI-compatible APIs
        image_msg = HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                },
            },
        ])

        return tool_msg, image_msg

    return ToolMessage(content=str(result), tool_call_id=call_id), None


def _get_current_url() -> str:
    """Safely get the current page URL."""
    try:
        page = _get_page()
        return page.url
    except Exception:
        return ""



def worker_node(state):
    print("============worker_node (PLAN MODE)==============")

    goal = state.get("goal", "")
    plan = state.get("plan", {})

    history = list(state.get("worker_history", []))
    messages = list(state.get("worker_messages", []))

    url_before = state.get("url", "") or _get_current_url()

    # ----------------------------
    # 1. WORKER INPUT = ONLY PLAN
    # ----------------------------
    if not messages:
        messages = worker_prompt.invoke({
            "goal": goal,
            "plan": str(plan),
            "history": "\n".join(history) if history else ""
        }).to_messages()

    # ----------------------------
    # 2. CALL LLM (with tools enabled)
    # ----------------------------
    response = worker_llm_with_tools.invoke(messages)

    messages.append(response)

    # ----------------------------
    # 3. LOGGING (skip image content to avoid huge logs)
    # ----------------------------
    with open("output/llm_log.txt", "w", encoding="utf-8") as f:
        for m in messages:
            content = m.content
            # Truncate image content blocks for logging
            if isinstance(content, list):
                log_content = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "image_url":
                        log_content.append("[IMAGE CONTENT BLOCK]")
                    else:
                        log_content.append(block)
                f.write(f"{m.type}:\n{log_content}\n\n")
            else:
                f.write(f"{m.type}:\n{content}\n\n")
        f.write("\n===== RESPONSE =====\n")
        f.write(str(response.content))

    # ----------------------------
    # 4. HANDLE TOOL CALLS
    # ----------------------------
    tool_calls = getattr(response, "tool_calls", None) or []

    if not tool_calls:
        return {
            "worker_history": history + [f"[FINAL] {response.content}"],
            "worker_messages": messages,
            "next_action": "end",
        }

    tc = tool_calls[0]
    tool_name = tc["name"]

    tool_msg, image_msg = _execute_tool_call(tc)
    messages.append(tool_msg)

    # If screenshot was taken, inject the image as a follow-up HumanMessage
    if image_msg is not None:
        messages.append(image_msg)
        history_entry = f"{tool_name}({tc['args']}) → [screenshot image]"
    else:
        history_entry = f"{tool_name}({tc['args']}) → {str(tool_msg.content)[:300]}"
    history.append(history_entry)

    # ----------------------------
    # 5. DETECT NAVIGATION
    # ----------------------------
    next_action = "worker"

    if tool_name in ("navigate_tool", "click_tool", "go_back_tool", "press_key_tool"):
        url_after = _get_current_url()
        if url_after and url_after != url_before:
            next_action = "worker"

    return {
        "worker_history": history,
        "worker_messages": messages,
        "next_action": next_action,
    }
