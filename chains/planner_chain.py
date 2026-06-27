from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage
from llm.model import model

from prompts.planner_prompt import planner_prompt
from prompts.final_prompt import final_prompt

parser_str = StrOutputParser()
parser_json = JsonOutputParser()


def build_planner_messages(goal: str, page_data: str, image_base64: str = None):
    """Build messages for the planner, injecting image into the human message if available."""
    base_messages = planner_prompt.invoke({
        "goal": goal,
        "page_data": page_data,
    }).to_messages()

    if image_base64:
        # Replace the human message content with multimodal content blocks
        human_text = base_messages[-1].content
        base_messages[-1] = HumanMessage(content=[
            {"type": "text", "text": human_text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                },
            },
        ])

    return base_messages


def planner_chain_invoke(goal: str, page_data: str, image_base64: str = None):
    """Invoke the planner with multimodal messages and parse JSON output."""
    messages = build_planner_messages(goal, page_data, image_base64)
    response = model.invoke(messages)
    return parser_json.parse(response.content)


# Final answer chain (unchanged — text only)
final_chain = final_prompt | model | parser_str
