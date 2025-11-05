#!/usr/bin/env python3
"""Debug templating issue"""

import sys
from pathlib import Path

app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import AdvancedTemplatingEngine

engine = AdvancedTemplatingEngine()

# Test with missing variables
template = "Hello {{name}}, your {{missing_var}} is ready!"
variables = {"name": "Charlie"}

result = engine.render_template(template, variables)

print(f"Success: {result.success}")
print(f"Content: {result.rendered_content}")
print(f"Error: {result.error}")