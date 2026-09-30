from .ai_service import plan_model as model

# Function to generate workout
def generate_workout_gemini(user_input):
    if hasattr(user_input, "goal"):
        goal = user_input.goal
        intensity = user_input.intensity
    elif isinstance(user_input, dict):
        goal = user_input.get("goal", "")
        intensity = user_input.get("intensity", "")
    else:
        goal = str(user_input)
        intensity = "medium"

    prompt = f"""
You are a professional fitness trainer.

Create a personalized, structured 7-day workout plan for someone with the goal of **{goal}**, and prefers **{intensity}** intensity workouts.

Each day must include:
- A warm-up (5-10 mins)
- Main workout (targeted exercises, sets & reps)
- Cooldown or recovery tip

Format:
Day 1:
Warm-up: ...
Main Workout: ...
Cooldown: ...
(Repeat for Day 2-7)
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"
