import os
from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .database import (
    SessionLocal,
    User,
    WorkoutPlan,
    save_user,
    save_plan,
    update_plan,
    get_original_plan,
    get_plan,
    get_user,
    get_all_users,
    get_all_plans,
    delete_user,
)
from .gemini_generator import generate_workout_gemini
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .updated_plan import update_workout_plan
from .schemas import (
    WorkoutRequest,
    UserInput,
    FeedbackRequest,
    FeedbackResponse,
    GenerateResponse,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
template_dir = str(BASE_DIR / "templates") if (BASE_DIR / "templates").exists() else str(BASE_DIR.parent / "templates")
templates = Jinja2Templates(directory=template_dir)


# -------------------------------------------------------------
# Web Routes
# -------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Displays the user form via index.html"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.get("/generate-workout", response_class=HTMLResponse)
def get_generate_workout(request: Request):
    return RedirectResponse(url="/", status_code=303)


@router.get("/submit-feedback", response_class=HTMLResponse)
def get_submit_feedback(request: Request):
    return RedirectResponse(url="/", status_code=303)


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    name: str = Form(None),
    username: str = Form(None),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    """Processes user input and generates a personalized workout plan & nutrition tip."""
    try:
        user_name = name or username or f"User_{user_id}"
        user_data = {
            "name": user_name,
            "username": user_name,
            "user_id": user_id,
            "age": age,
            "weight": weight,
            "goal": goal,
            "intensity": intensity,
        }

        # Generate 7-day workout plan using Gemini
        workout_plan = generate_workout_gemini({
            "goal": goal,
            "intensity": intensity,
        })

        # Generate nutrition tip using Gemini Flash
        nutrition_tip = generate_nutrition_tip_with_flash(goal)

        # Save user and workout plan to database
        save_user(
            user_id=user_id,
            name=user_name,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )
        save_plan(user_id=user_id, plan=workout_plan, nutrition_tip=nutrition_tip)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "username": user_name,
                "name": user_name,
                "user_id": user_id,
                "age": age,
                "weight": weight,
                "goal": goal,
                "intensity": intensity,
                "workout_plan": workout_plan,
                "nutrition_tip": nutrition_tip,
                "updated_plan": None,
                "feedback": None,
                "plan_updated": False,
                "user": user_data,
            },
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(exc)},
            status_code=500,
        )


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
):
    """Updates the workout plan based on user feedback."""
    try:
        original = get_original_plan(user_id)
        user = get_user(user_id)
        plan_record = get_plan(user_id)

        if not original:
            original = "No original plan found for this user."

        # Generate updated plan using Gemini
        updated = update_workout_plan(original, feedback)

        # Update in database
        update_plan(user_id, updated, feedback)

        nutrition_tip = (
            plan_record.nutrition_tip
            if plan_record and plan_record.nutrition_tip
            else generate_nutrition_tip_with_flash(user.goal if user else "wellness")
        )

        user_name = user.name if user else f"User {user_id}"
        age = user.age if user else "N/A"
        weight = user.weight if user else "N/A"
        goal = user.goal if user else "N/A"
        intensity = user.intensity if user else "N/A"

        user_dict = {
            "name": user_name,
            "username": user_name,
            "user_id": user_id,
            "age": age,
            "weight": weight,
            "goal": goal,
            "intensity": intensity,
        }

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "username": user_name,
                "name": user_name,
                "user_id": user_id,
                "age": age,
                "weight": weight,
                "goal": goal,
                "intensity": intensity,
                "workout_plan": original,
                "updated_plan": updated,
                "nutrition_tip": nutrition_tip,
                "feedback": feedback,
                "plan_updated": True,
                "success_message": "Your plan has been updated based on your feedback!",
                "user": user_dict,
            },
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(exc)},
            status_code=500,
        )


# # 8. Web: View all users & their plans
@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    """Displays an admin dashboard showing all users and their plans."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        user_data = []
        for user in users:
            plan = db.query(WorkoutPlan).filter(
                (WorkoutPlan.user_id == str(user.id)) | (WorkoutPlan.user_id == user.user_id)
            ).order_by(WorkoutPlan.id.desc()).first()

            user_data.append({
                "id": user.id,
                "user_id": user.user_id or user.id,
                "name": user.name,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,
                "original_plan": plan.original_plan if plan else "N/A",
                "updated_plan": plan.updated_plan if plan and plan.updated_plan else "Not updated",
            })

        return templates.TemplateResponse(
            request=request,
            name="all_users.html",
            context={"users": user_data},
        )
    finally:
        db.close()


@router.post("/delete-user/{user_id}")
def remove_user(user_id: str):
    delete_user(user_id)
    return RedirectResponse(url="/view-all-users", status_code=303)


# -------------------------------------------------------------
# Document Guided API Endpoints
# -------------------------------------------------------------

# # 1. API: Generate workout using Gemini Pro
@router.post("/generate-workout/gemini")
async def generate_gemini_workout(request: WorkoutRequest):
    try:
        result = generate_workout_gemini({
            "goal": request.goal,
            "intensity": request.intensity,
        })
        return {"model": "gemini-pro", "workout_plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # 2. API: Generate nutrition tip using Gemini Flash
@router.get("/nutrition-tip")
def get_flash_tip(goal: str):
    tip = generate_nutrition_tip_with_flash(goal)
    return {"goal": goal, "nutrition_tip": tip}


# # 3. API: Save user info & generate plan
@router.post("/generate-plan")
def generate_plan(user_data: UserInput):
    try:
        save_user(
            user_id=user_data.user_id,
            name=user_data.username or user_data.name,
            age=user_data.age,
            weight=user_data.weight,
            goal=user_data.goal,
            intensity=user_data.intensity,
        )
        plan = generate_workout_gemini({
            "goal": user_data.goal,
            "intensity": user_data.intensity,
        })
        save_plan(user_data.user_id, plan)
        return {
            "message": "Workout plan generated and saved successfully!",
            "workout_plan": plan,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


# # 4. API: Update workout plan based on user feedback
@router.post("/update-plan/{user_id}", response_model=dict)
def update_user_plan(user_id: str, data: FeedbackRequest):
    original = get_original_plan(user_id)
    if not original:
        return {"error": "Original plan not found for this user."}
    updated = update_workout_plan(original, data.feedback)
    update_plan(user_id, updated, data.feedback)
    return {"updated_plan": updated}


# -------------------------------------------------------------
# JSON API compatibility endpoints
# -------------------------------------------------------------

@router.post("/api/generate-workout", response_model=GenerateResponse)
def api_generate_workout(payload: UserInput):
    try:
        plan = generate_workout_gemini(payload)
        tip = generate_nutrition_tip_with_flash(payload)
        name = payload.username or payload.name
        save_user(
            user_id=payload.user_id,
            name=name,
            age=payload.age,
            weight=payload.weight,
            goal=payload.goal,
            intensity=payload.intensity,
        )
        save_plan(payload.user_id, plan, tip)
        return GenerateResponse(
            user_id=payload.user_id,
            workout_plan=plan,
            nutrition_tip=tip,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/submit-feedback", response_model=FeedbackResponse)
def api_submit_feedback(payload: FeedbackRequest):
    user = get_user(payload.user_id)
    plan = get_plan(payload.user_id)
    if not user or not plan:
        raise HTTPException(status_code=404, detail="User ID not found.")

    try:
        revised = update_workout_plan(plan.original_plan, payload.feedback)
        update_plan(payload.user_id, revised, payload.feedback)
        return FeedbackResponse(
            user_id=payload.user_id,
            updated_plan=revised,
            nutrition_tip=plan.nutrition_tip,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/users")
def api_users():
    users = get_all_users()
    plans = {str(plan.user_id): plan for plan in get_all_plans()}
    return {
        "users": [
            {
                "user_id": user.user_id or user.id,
                "name": user.name,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,
                "created_at": user.created_at,
                "original_plan": plans.get(str(user.user_id or user.id)).original_plan if plans.get(str(user.user_id or user.id)) else None,
                "updated_plan": plans.get(str(user.user_id or user.id)).updated_plan if plans.get(str(user.user_id or user.id)) else None,
            }
            for user in users
        ]
    }


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "ai_mode": "mock" if settings.mock_ai or not settings.gemini_api_key else "gemini",
        "plan_model": settings.gemini_plan_model,
        "tip_model": settings.gemini_tip_model,
    }
