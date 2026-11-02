"""Farmer registration, login and profile (Module 1: Farmer Management)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.locations import match
from ..database import get_db
from ..deps import get_current_farmer
from ..models import Farmer, Language, Role
from ..schemas import FarmerLogin, FarmerOut, FarmerRegister, FarmerUpdate, TokenOut
from ..security import (
    create_access_token, hash_password, password_problems, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def _require_strong(password: str, name: str, phone: str) -> None:
    """Refuse a weak password, naming the first rule it breaks."""
    problems = password_problems(password, name=name, phone=phone)
    if problems:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=problems[0])


def _area(value: str | None) -> str:
    """The canonical area name, so weather and advice always resolve to it."""
    name = match(value or "Thyolo")
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose an area in Thyolo or Mulanje district.",
        )
    return name


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: FarmerRegister, db: Session = Depends(get_db)):
    existing = db.scalar(select(Farmer).where(Farmer.phone == payload.phone))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer is already registered with this phone number.",
        )

    _require_strong(payload.password, payload.name, payload.phone)

    farmer = Farmer(
        name=payload.name.strip(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        location=_area(payload.location),
        language=Language(payload.language),
        farm_size_ha=payload.farm_size_ha,
        years_farming=payload.years_farming,
        role=Role.FARMER,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    token = create_access_token(farmer.farmer_id, farmer.role.value)
    return TokenOut(access_token=token, farmer=FarmerOut.model_validate(farmer))


@router.post("/login", response_model=TokenOut)
def login(payload: FarmerLogin, db: Session = Depends(get_db)):
    farmer = db.scalar(select(Farmer).where(Farmer.phone == payload.phone))
    if not farmer or not verify_password(payload.password, farmer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phone number or password is incorrect.",
        )
    if not farmer.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This account has been disabled.")

    token = create_access_token(farmer.farmer_id, farmer.role.value)
    return TokenOut(access_token=token, farmer=FarmerOut.model_validate(farmer))


@router.get("/me", response_model=FarmerOut)
def me(farmer: Farmer = Depends(get_current_farmer)):
    return FarmerOut.model_validate(farmer)


@router.patch("/me", response_model=FarmerOut)
def update_me(
    payload: FarmerUpdate,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    if payload.name is not None:
        farmer.name = payload.name.strip()
    if payload.location is not None:
        farmer.location = _area(payload.location)
    if payload.language is not None:
        language = payload.language.upper()
        if language not in {"EN", "NY"}:
            raise HTTPException(status_code=422, detail="Language must be EN or NY")
        farmer.language = Language(language)
    if payload.farm_size_ha is not None:
        farmer.farm_size_ha = payload.farm_size_ha
    if payload.years_farming is not None:
        farmer.years_farming = payload.years_farming

    db.commit()
    db.refresh(farmer)
    return FarmerOut.model_validate(farmer)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Change the password; the new one must meet the same strength rules."""
    if not verify_password(payload.current_password, farmer.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Your current password is not correct.")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Choose a password different from your current one.")
    _require_strong(payload.new_password, farmer.name, farmer.phone)
    farmer.password_hash = hash_password(payload.new_password)
    db.commit()
