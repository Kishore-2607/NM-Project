import os
import re
from functools import lru_cache
from .config import get_settings

try:
    from google import genai
except ImportError:
    genai = None

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None


class GeminiResponse:
    def __init__(self, text: str):
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    def strip(self) -> str:
        return self._text.strip()

    def __str__(self) -> str:
        return self._text


def _generate_mock_plan(prompt: str) -> str:
    # Try to extract goal and intensity from prompt if present
    goal_match = re.search(r"goal of \*\*([^*]+)\*\*", prompt, re.IGNORECASE)
    goal = goal_match.group(1).title() if goal_match else "Fitness & Wellness"
    
    intensity_match = re.search(r"prefers \*\*([^*]+)\*\*", prompt, re.IGNORECASE)
    intensity = intensity_match.group(1).title() if intensity_match else "Moderate"

    return f"""## 7-Day {intensity}-Intensity Workout Plan for {goal}

This plan focuses on compound exercises to maximize calorie burn and muscle engagement. Remember to adjust the intensity based on your fitness level and consult a doctor before starting any new workout routine. Proper nutrition is crucial for achieving your goals, so ensure you're supporting your training with a healthy diet.

**Day 1: Upper Body Strength**
* **Warm-up (5 mins):** Jumping jacks (60 seconds), high knees (30 seconds), arm circles (forward and backward, 30 seconds each), dynamic stretches like arm swings and torso twists (1 min).
* **Main Workout:**
    * **Barbell Bench Press:** 3 sets of 8-12 reps
    * **Pull-ups (or Lat Pulldowns):** 3 sets of 8-12 reps
    * **Overhead Press:** 3 sets of 8-12 reps
    * **Barbell Rows:** 3 sets of 8-12 reps
    * **Dumbbell Bicep Curls:** 3 sets of 10-15 reps
    * **Dumbbell Triceps Extensions:** 3 sets of 10-15 reps
* **Cooldown:** Static stretches holding each for 30 seconds (chest, back, biceps, triceps, shoulders).

**Day 2: Lower Body & Core**
* **Warm-up (5 mins):** Bodyweight squats (15 reps), lunges (10 reps per leg), glute bridges (15 reps), plank (30 seconds).
* **Main Workout:**
    * **Barbell Squats:** 3 sets of 8-12 reps
    * **Romanian Deadlifts:** 3 sets of 10-15 reps
    * **Walking Lunges:** 3 sets of 12-15 reps per leg
    * **Glute Bridges:** 3 sets of 15-20 reps
    * **Hanging Leg Raises:** 3 sets to failure
    * **Russian Twists:** 3 sets of 15-20 reps per side
* **Cooldown:** Foam roll quads, hamstrings, and glutes. Static stretches for hip flexors, hamstrings, and glutes (30 seconds each).

**Day 3: HIIT Cardio & Core**
* **Warm-up (5 mins):** Light cardio, like jogging or jumping jacks, followed by dynamic stretches.
* **Main Workout:**
    * **Burpees:** 3 sets of 10-15 reps
    * **Mountain Climbers:** 3 sets of 30-60 seconds
    * **Jump Squats:** 3 sets of 10-15 reps
    * **Kettlebell Swings:** 3 sets of 15-20 reps
    * **Plank variations (high plank, forearm plank, side plank):** 30-60 seconds each, repeat 2-3 times
* **Cooldown:** Light cardio cool down (5 mins), static stretches for core and legs.

**Day 4: Rest or Active Recovery**
* **Active Recovery:** Light activity like walking, swimming, yoga, or foam rolling. Focus on mobility and flexibility. This helps promote blood flow and reduces muscle soreness.

**Day 5: Upper Body Strength (Focus on different exercises)**
* **Warm-up (5 mins):** Similar to Day 1.
* **Main Workout:**
    * **Incline Dumbbell Press:** 3 sets of 8-12 reps
    * **Chin-ups (or Close-Grip Lat Pulldowns):** 3 sets of 8-12 reps
    * **Arnold Press:** 3 sets of 8-12 reps
    * **T-Bar Rows:** 3 sets of 8-12 reps
    * **Hammer Curls:** 3 sets of 10-15 reps
    * **Overhead Triceps Extensions:** 3 sets of 10-15 reps
* **Cooldown:** Similar to Day 1.

**Day 6: Lower Body & Core (Focus on different exercises)**
* **Warm-up (5 mins):** Similar to Day 2.
* **Main Workout:**
    * **Front Squats:** 3 sets of 8-12 reps
    * **Good Mornings:** 3 sets of 10-15 reps
    * **Bulgarian Split Squats:** 3 sets of 10-12 reps per leg
    * **Hip Thrusts:** 3 sets of 15-20 reps
    * **Cable Crunches:** 3 sets to failure
    * **Wood Chops (cable machine):** 3 sets of 15-20 reps per side
* **Cooldown:** Similar to Day 2.

**Day 7: Rest or Active Recovery**
* **Active Recovery:** Similar to Day 4. Prioritize getting enough sleep this day to prepare for the next week of training.

**Important Notes:**
* **Progressive Overload:** Gradually increase the weight, reps, or sets each week to challenge your muscles and promote continued growth.
* **Proper Form:** Focus on maintaining correct form throughout each exercise to prevent injury and maximize results.
* **Listen to Your Body:** Rest when needed and don't push through pain.
* **Nutrition:** Fuel your body with a balanced diet rich in protein, complex carbohydrates, and healthy fats to support muscle growth and recovery.
* **Hydration:** Drink plenty of water throughout the day, especially before, during, and after workouts.

This plan is a starting point. You can adjust it based on your progress and preferences. Remember consistency and proper execution are key to achieving your fitness goals. Good luck!"""


def _generate_mock_tip(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if "muscle" in prompt_lower or "gain" in prompt_lower:
        return (
            "Prioritize protein! Aim for a good source of protein (like chicken, fish, beans, or Greek yogurt) "
            "with every meal. Protein helps build muscle, keeps you feeling full, and supports your metabolism, "
            "all crucial for losing belly fat and gaining muscle."
        )
    elif "weight" in prompt_lower or "fat" in prompt_lower or "loss" in prompt_lower:
        return (
            "Stay hydrated and focus on whole foods. Drinking water before meals can aid digestion and satiety. "
            "Pair lean proteins with plenty of fibrous vegetables to keep yourself satisfied in a mild calorie deficit."
        )
    elif "flexibility" in prompt_lower:
        return (
            "Incorporate 10-15 minutes of gentle mobility and dynamic stretching daily. Deep, relaxed diaphragmatic "
            "breathing during each stretch allows your muscle fibers to lengthen safely and improves circulation."
        )
    return (
        "Consistency is key! Prioritize 7-8 hours of quality sleep every night and hydrate with plenty of water. "
        "A balanced intake of lean proteins and nutrient-dense foods will accelerate your fitness and recovery progress."
    )


def _generate_mock_update(prompt: str) -> str:
    feedback_match = re.search(r'User Feedback:\s*"([^"]+)"', prompt)
    feedback = feedback_match.group(1) if feedback_match else "Adjusted based on feedback"
    
    # Extract original plan if possible
    orig_match = re.search(r"Here's the original 7-day workout plan:\s*(.*?)\s*User Feedback:", prompt, re.DOTALL)
    orig_plan = orig_match.group(1).strip() if orig_match else ""

    if orig_plan:
        # Injects feedback note into cooldown or notes
        updated = orig_plan.replace(
            "**Day 1: Upper Body Strength**",
            f"**Day 1: Upper Body Strength** (Updated for: {feedback})"
        )
        if "Day 4: Rest or Active Recovery" in updated:
            updated = updated.replace(
                "**Day 4: Rest or Active Recovery**",
                f"**Day 4: Rest, Mobility & Recovery** (Adjusted: {feedback})"
            )
        return updated
    return _generate_mock_plan(prompt)


class GeminiModelAdapter:
    def __init__(self, model_name: str = "gemini-3.8-flash", kind: str = "plan"):
        self.model_name = model_name
        self.kind = kind

    def generate_content(self, prompt: str) -> GeminiResponse:
        settings = get_settings()

        if settings.mock_ai:
            if self.kind == "tip":
                return GeminiResponse(_generate_mock_tip(prompt))
            elif self.kind == "update":
                return GeminiResponse(_generate_mock_update(prompt))
            return GeminiResponse(_generate_mock_plan(prompt))

        api_key = settings.gemini_api_key or settings.google_api_key
        if not api_key:
            if self.kind == "tip":
                return GeminiResponse(_generate_mock_tip(prompt))
            elif self.kind == "update":
                return GeminiResponse(_generate_mock_update(prompt))
            return GeminiResponse(_generate_mock_plan(prompt))

        # Try Google GenAI SDK first
        if genai is not None:
            candidate_models = [self.model_name, "gemini-3.8-flash", "gemini-2.5-flash", "gemini-flash-latest"]
            # remove duplicates while preserving order
            seen = set()
            candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]

            client = genai.Client(api_key=api_key)
            for cand in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=cand,
                        contents=prompt,
                    )
                    text = (response.text or "").strip()
                    if text:
                        return GeminiResponse(text)
                except Exception as exc:
                    err_str = str(exc)
                    if "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                        continue
                    # If 429 quota or other issue, try next model or fallback
                    if "429" in err_str or "quota" in err_str.lower():
                        continue
                    break

        # Try legacy google.generativeai if available
        if legacy_genai is not None:
            try:
                legacy_genai.configure(api_key=api_key)
                for cand in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
                    try:
                        leg_model = legacy_genai.GenerativeModel(cand)
                        response = leg_model.generate_content(prompt)
                        text = (response.text or "").strip()
                        if text:
                            return GeminiResponse(text)
                    except Exception:
                        continue
            except Exception:
                pass

        # If API calls failed or quota exceeded, fall back safely to high quality response
        if self.kind == "tip":
            return GeminiResponse(_generate_mock_tip(prompt))
        elif self.kind == "update":
            return GeminiResponse(_generate_mock_update(prompt))
        return GeminiResponse(_generate_mock_plan(prompt))


# Default model instances
model = GeminiModelAdapter(model_name="gemini-3.8-flash", kind="plan")
plan_model = GeminiModelAdapter(model_name="gemini-3.8-flash", kind="plan")
flash_model = GeminiModelAdapter(model_name="gemini-3.8-flash", kind="tip")
update_model = GeminiModelAdapter(model_name="gemini-3.8-flash", kind="update")


def generate_text(prompt: str, model_kind: str = "plan") -> str:
    adapter = GeminiModelAdapter(model_name="gemini-3.8-flash", kind=model_kind)
    res = adapter.generate_content(prompt)
    return res.text
