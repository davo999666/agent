from state import BrowserState


def worker_router(state: BrowserState):
    """Route after worker executes one action.

    Returns:
        - "browser": page URL changed → re-extract/chunk/embed
        - "worker": same page → continue worker loop
        - "end": task is complete
    """
    return state.get("next_action", "end")


