"""
A/B Testing Framework
====================

Statistical comparison framework for prompt testing and analysis.
"""

import logging
import statistics
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .llm_provider_abstraction import LLMResponse
from .scoring_engine import EvaluationResult, ScoringRubric
from .multi_model_testing import TestSession, TestConfiguration
from ...models.base import generate_id


class ABTestStatus(Enum):
    """Status of A/B tests."""
    DRAFT = "draft"
    