#!/usr/bin/env python3
"""Debug complexity issue"""

import sys
from pathlib import Path

app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import AdvancedTemplatingEngine

engine = AdvancedTemplatingEngine()

complex_template = """
{% if user.premium %}
Hello {{user.name|title}}, welcome to our premium service!

Your benefits include:
{% for benefit in premium_benefits %}
- {{benefit.name}}: {{benefit.description}}
{% endfor %}

{% if user.credits > 100 %}
You have {{user.credits}} credits remaining.
{% endif %}

{% else %}
Hello {{user.name}}, welcome to our standard service!
{% endif %}

Today's date: {{current_date}}
"""

info = engine.get_template_info(complex_template)

print(f"Variables count: {info['variables_count']}")
print(f"Variables: {info['variables']}")
print(f"Complexity score: {info['complexity_score']}")
print(f"Is valid: {info['is_valid']}")
print(f"Errors: {info['errors']}")
print(f"Warnings: {info['warnings']}")