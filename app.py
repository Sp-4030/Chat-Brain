"""Streamlit Dashboard Entrypoint for ChatBrain.

Delegates execution to the modular dashboard implementation in dashboard/app.py
while maintaining backwards compatibility for existing launch scripts.
"""

import os
import runpy

dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
runpy.run_path(dashboard_path, run_name="__main__")