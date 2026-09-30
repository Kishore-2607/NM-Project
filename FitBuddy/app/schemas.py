from typing import Optional, Union
from pydantic import BaseModel, Field, model_validator


class WorkoutRequest(BaseModel):
    goal: str
    intensity: str


class UserInput(BaseModel):
    user_id: Union[int, str]
    username: Optional[str] = None
    name: Optional[str] = None
    age: int
    weight: float
    goal: str
    intensity: str

    @model_validator(mode="before")
    @classmethod
    def reconcile_name_username(cls, data):
        if isinstance(data, dict):
            if "name" in data and not data.get("username"):
                data["username"] = data["name"]
            elif "username" in data and not data.get("name"):
                data["name"] = data["username"]
        return data


class FeedbackRequest(BaseModel):
    user_id: Optional[Union[int, str]] = None
    feedback: str


class GenerateResponse(BaseModel):
    user_id: Union[int, str]
    workout_plan: str
    nutrition_tip: str


class FeedbackResponse(BaseModel):
    user_id: Union[int, str]
    updated_plan: str
    nutrition_tip: Optional[str] = None
