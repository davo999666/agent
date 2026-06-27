from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from llm.model import model

from prompts.planner_prompt import planner_prompt
from prompts.final_prompt import final_prompt

parser_str = StrOutputParser()
parser_json = JsonOutputParser()

# Planner chain — text only
planner_chain = planner_prompt | model | parser_json

# Final answer chain — text only
final_chain = final_prompt | model | parser_str
