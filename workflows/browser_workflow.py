from langgraph.graph import StateGraph, END

from state import BrowserState
from nodes.planner_node import planner_node
from nodes.worker_node import worker_node
from workflows.routers import worker_router


class BrowserWorkflow:
    """
    Minimal agent system:

    planner → worker loop
    """

    def __init__(self):
        graph = StateGraph(BrowserState)

        # -------------------
        # NODES
        # -------------------
        graph.add_node("planner", planner_node)
        graph.add_node("worker", worker_node)

        # -------------------
        # ENTRY POINT
        # -------------------
        graph.set_entry_point("planner")

        # -------------------
        # FLOW
        # -------------------
        graph.add_edge("planner", "worker")

        # -------------------
        # WORKER LOOP
        # -------------------
        graph.add_conditional_edges(
            "worker",
            worker_router,
            {
                "worker": "worker",  # continue working
                "end": END,          # finish task
            },
        )

        self.app = graph.compile()

    def run(self, goal: str, start_url: str):
        result = self.app.invoke(
            {
                "goal": goal,
                "start_url": start_url,
            }
        )

        worker_history = result.get("worker_history", [])

        # save logs
        with open("output/worker_history.txt", "w", encoding="utf-8") as f:
            for entry in worker_history:
                f.write(entry + "\n")

        return result