from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from llm.model import model

from prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, PLANNER_HUMAN_TEMPLATE
from prompts.final_prompt import final_prompt

parser_str = StrOutputParser()
parser_json = JsonOutputParser()


def build_planner_messages(goal: str, page_data: str, image_base64: str = None):
    """Build multimodal messages for the planner, including an image if available."""
    system_msg = SystemMessage(content=PLANNER_SYSTEM_PROMPT)

    human_text = PLANNER_HUMAN_TEMPLATE.format(goal=goal, page_data=page_data)

    if image_base64:
        human_content = [
            {"type": "text", "text": human_text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                },
            },
        ]
    else:
        human_content = [{"type": "text", "text": human_text}]

    human_msg = HumanMessage(content=human_content)
    return [system_msg, human_msg]


def planner_chain_invoke(goal: str, page_data: str, image_base64: str = None):
    """Invoke the planner with multimodal messages and parse JSON output."""
    messages = build_planner_messages(goal, page_data, image_base64)
    response = model.invoke(messages)
    return parser_json.parse(response.content)


# Final answer chain (unchanged — text only)
final_chain = final_prompt | model | parser_str
