from .ai_service import flash_model as model

def generate_nutrition_tip_with_flash(goal: str) -> str:
    """
    Generate a nutrition or recovery tip using Gemini Flash based on the user's fitness goal.

    Args:
        goal (str): User's fitness goal - "weight loss", "muscle gain", or "general fitness".

    Returns:
        str: Generated tip.
    """
    if hasattr(goal, "goal"):
        goal_text = goal.goal
    elif isinstance(goal, dict):
        goal_text = goal.get("goal", "")
    else:
        goal_text = str(goal)

    prompt = (
        f"Give one clear, helpful nutrition or recovery tip for someone focused on '{goal_text}'. "
        "The tip should be practical, friendly, and easy to understand."
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating tip: {str(e)}"
