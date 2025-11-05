#!/usr/bin/env python3
"""Debug validation issue"""

import sys
from pathlib import Path

app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import AdvancedTemplatingEngine, TemplateVariable

engine = AdvancedTemplatingEngine()

template = "Hello {{name}}, your order {{order_id}} is {{status}}."
variables_def = [
    TemplateVariable(name="name", type="string"),
    TemplateVariable(name="order_id", type="string"),
    TemplateVariable(name="unused_var", type="string")
]

validation = engine.validate_template(template, variables_def)

print(f"Is valid: {validation.is_valid}")
print(f"Errors: {validation.errors}")
print(f"Warnings: {validation.warnings}")
print(f"Variables found: {validation.variables_found}")
print(f"Variables missing: {validation.variables_missing}")