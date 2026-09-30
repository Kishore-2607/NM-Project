from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, select, or_, text, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    intensity = Column(String, nullable=False)
    schedule = Column(Integer, default=7)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WorkoutPlan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    original_plan = Column(Text, nullable=False)
    updated_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)


# Alias Plan for backwards and test compatibility
Plan = WorkoutPlan


def init_db() -> None:
    Path("fitbuddy.db").parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Ensure missing columns in existing SQLite DB are automatically migrated
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN schedule INTEGER DEFAULT 7"))
            conn.commit()
        except Exception:
            pass


def save_user(
    user_id=None,
    name: str = None,
    age: int = None,
    weight: float = None,
    goal: str = None,
    intensity: str = None,
    schedule: int = 7,
    **kwargs,
):
    """
    Saves or updates user information.
    Accepts either positional arguments, keyword arguments (user_id=...), or a dictionary payload.
    """
    if isinstance(user_id, dict):
        data = user_id
        raw_uid = data.get("user_id") or data.get("id")
        name = data.get("name") or data.get("username", "")
        age = int(data.get("age", 25))
        weight = float(data.get("weight", 70.0))
        goal = data.get("goal", "")
        intensity = data.get("intensity", "medium")
        schedule = int(data.get("schedule", 7))
    else:
        raw_uid = user_id if user_id is not None else kwargs.get("user_id_or_data", "")

    name = name or kwargs.get("username", "") or f"User_{raw_uid}"
    if age is None:
        age = int(kwargs.get("age", 25))
    if weight is None:
        weight = float(kwargs.get("weight", 70.0))
    if goal is None:
        goal = str(kwargs.get("goal", "general wellness"))
    if intensity is None:
        intensity = str(kwargs.get("intensity", "medium"))

    # Parse numeric ID if possible for SQLite integer primary key
    numeric_id = None
    try:
        numeric_id = int(str(raw_uid).strip())
    except (ValueError, TypeError):
        numeric_id = abs(hash(str(raw_uid))) % 1000000

    db = SessionLocal()
    try:
        existing = db.query(User).filter(
            or_(User.id == numeric_id, User.user_id == str(raw_uid))
        ).first()

        if existing:
            # Update existing user info
            existing.name = name
            existing.age = age
            existing.weight = weight
            existing.goal = goal
            existing.intensity = intensity
            existing.schedule = schedule
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create a new user
            user = User(
                id=numeric_id,
                user_id=str(raw_uid),
                name=name,
                age=age,
                weight=weight,
                goal=goal,
                intensity=intensity,
                schedule=schedule,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
    finally:
        db.close()


def save_plan(user_id=None, plan: str = None, nutrition_tip: str = None, original_plan: str = None, **kwargs):
    """Stores the plan in the database."""
    uid = user_id if user_id is not None else kwargs.get("uid")
    plan_text = plan or original_plan or kwargs.get("plan_text", "")
    tip_text = nutrition_tip or kwargs.get("tip", "")

    db = SessionLocal()
    try:
        workout = WorkoutPlan(
            user_id=str(uid),
            original_plan=plan_text,
            nutrition_tip=tip_text,
        )
        db.add(workout)
        db.commit()
        db.refresh(workout)
        return workout
    finally:
        db.close()


def update_plan(user_id=None, updated_text: str = None, feedback: str = None, updated_plan: str = None, **kwargs):
    """Update the plan based on feedback."""
    uid = user_id if user_id is not None else kwargs.get("uid")
    text = updated_text or updated_plan or kwargs.get("text", "")
    fb = feedback or kwargs.get("feedback_text")

    db = SessionLocal()
    try:
        workout = db.query(WorkoutPlan).filter(
            or_(WorkoutPlan.user_id == str(uid), WorkoutPlan.user_id == uid)
        ).order_by(WorkoutPlan.id.desc()).first()

        if workout:
            workout.updated_plan = text
            if fb:
                workout.feedback = fb
            workout.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(workout)
            return workout
        return None
    finally:
        db.close()


def get_original_plan(user_id=None, **kwargs):
    """Fetch the original plan for a user."""
    uid = user_id if user_id is not None else kwargs.get("uid")
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(
            or_(WorkoutPlan.user_id == str(uid), WorkoutPlan.user_id == uid)
        ).order_by(WorkoutPlan.id.desc()).first()
        return plan.original_plan if plan else None
    finally:
        db.close()


def get_plan(user_id=None, **kwargs):
    """Fetch the latest plan object for a user."""
    uid = user_id if user_id is not None else kwargs.get("uid")
    db = SessionLocal()
    try:
        return db.query(WorkoutPlan).filter(
            or_(WorkoutPlan.user_id == str(uid), WorkoutPlan.user_id == uid)
        ).order_by(WorkoutPlan.id.desc()).first()
    finally:
        db.close()


def get_user(user_id=None, **kwargs):
    """Fetch user record by ID."""
    uid = user_id if user_id is not None else kwargs.get("uid")
    db = SessionLocal()
    try:
        numeric_id = None
        try:
            numeric_id = int(str(uid).strip())
        except (ValueError, TypeError):
            pass

        if numeric_id is not None:
            return db.query(User).filter(
                or_(User.id == numeric_id, User.user_id == str(uid))
            ).first()
        return db.query(User).filter(User.user_id == str(uid)).first()
    finally:
        db.close()


def get_all_users() -> list[User]:
    """Retrieve all registered users."""
    db = SessionLocal()
    try:
        return db.query(User).order_by(User.id.asc()).all()
    finally:
        db.close()


def get_all_plans() -> list[WorkoutPlan]:
    """Retrieve all generated plans."""
    db = SessionLocal()
    try:
        return db.query(WorkoutPlan).order_by(WorkoutPlan.id.desc()).all()
    finally:
        db.close()


def delete_user(user_id=None, **kwargs) -> bool:
    """Delete a user and associated plans."""
    uid = user_id if user_id is not None else kwargs.get("uid")
    db = SessionLocal()
    try:
        numeric_id = None
        try:
            numeric_id = int(str(uid).strip())
        except (ValueError, TypeError):
            pass

        cond = or_(User.id == numeric_id, User.user_id == str(uid)) if numeric_id is not None else (User.user_id == str(uid))
        user = db.query(User).filter(cond).first()
        if not user:
            return False

        db.query(WorkoutPlan).filter(
            or_(WorkoutPlan.user_id == str(uid), WorkoutPlan.user_id == user.id)
        ).delete(synchronize_session=False)

        db.delete(user)
        db.commit()
        return True
    finally:
        db.close()
