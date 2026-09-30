"""
Handles nutrition-specific logic and helper functions for FitBuddy.
"""
from .gemini_flash_generator import generate_nutrition_tip_with_flash


def get_nutrition_guidance(goal: str) -> str:
    """
    Returns nutrition or recovery guidance aligned with the user's fitness goal.
    """
    return generate_nutrition_tip_with_flash(goal)
