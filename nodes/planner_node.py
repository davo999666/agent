import os
import time
import base64
from typing import Dict, Any
from pathlib import Path

from chains.planner_chain import planner_chain
from tools.browser_tools import take_screenshot


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("==============planner_node================")

    goal = state.get("goal", "")
    url = state.get("url", "")

    # ----------------------------
    # 1. TAKE SCREENSHOT (ONLY ONCE)
    # ----------------------------
    screenshot_result = take_screenshot.invoke({"dummy": ""})
    print(f"Screenshot taken: {bool(screenshot_result.get('image'))}")

    image_base64 = screenshot_result.get("image")

    image_path = None

    # ----------------------------
    # 2. SAVE IMAGE TO DISK
    # ----------------------------
    if image_base64:
        os.makedirs("output", exist_ok=True)

        image_bytes = base64.b64decode(image_base64)

        filename = f"screenshot_{int(time.time())}.png"
        image_path = Path("output") / filename

        with open(image_path, "wb") as f:
            f.write(image_bytes)

    # ----------------------------
    # 3. PAGE DATA (text context only — image sent separately)
    # ----------------------------
    page_data = f"URL: {url}\nScreenshot available: {bool(image_base64)}"

    # ----------------------------
    # 4. CALL PLANNER WITH IMAGE
    # ----------------------------
    result = planner_chain.invoke({
        "goal": goal,
        "page_data": page_data,
    })

    # ----------------------------
    # 5. SAVE PLAN
    # ----------------------------
    os.makedirs("output", exist_ok=True)

    with open("output/plan.txt", "w", encoding="utf-8") as f:
        f.write(str(result))

    return {
        "plan": result,
        "image_saved": True,
        "image_path": str(image_path) if image_path else None
    }
