"""Authentication router with PostgreSQL-backed sessions."""

from __future__ import annotations

from datetime import datetime
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user, get_db
from backend.modules.auth.models import AuthSession, User
from backend.modules.auth.security import (
    auth_rate_limiter,
    generate_session_token,
    get_session_expiry,
    hash_password,
    hash_session_token,
    normalize_email,
    validate_password_strength,
    verify_password,
)
from backend.modules.config import settings


router = APIRouter()
FULL_NAME_PATTERN = re.compile(r"^[A-Za-zÇĞİÖŞÜçğıöşüÂâÊêÎîÔôÛûÄäËëÏïÖöÜüŸÿ'\-.\s]+$")


class LoginRequest(BaseModel):
    """Login payload."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=3, max_length=128)


class SetupRequest(BaseModel):
    """Initial admin setup payload."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=3, max_length=128)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        if not FULL_NAME_PATTERN.fullmatch(value):
            raise ValueError(
                "Ad soyad alanında Türkçe karakterler kullanılabilir; yalnızca harf, boşluk, tire, nokta ve kesme işareti kabul edilir."
            )
        return value


class ProfileUpdateRequest(BaseModel):
    """Profile update payload."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=255)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        if not FULL_NAME_PATTERN.fullmatch(value):
            raise ValueError(
                "Ad soyad alanında Türkçe karakterler kullanılabilir; yalnızca harf, boşluk, tire, nokta ve kesme işareti kabul edilir."
            )
        return value


class PasswordChangeRequest(BaseModel):
    """Password change payload."""

    current_password: str = Field(min_length=3, max_length=128)
    new_password: str = Field(min_length=3, max_length=128)


class DeleteAccountRequest(BaseModel):
    """Delete-account payload."""

    current_password: str = Field(min_length=3, max_length=128)


def _serialize_user(user: User) -> dict[str, str]:
    """Return safe user payload for frontend."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


def _get_active_user_count(db: Session) -> int:
    """Return active user count."""
    return db.scalar(select(func.count()).select_from(User)) or 0


def _set_auth_cookie(response: Response, token: str) -> None:
    """Attach secure auth cookie."""
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.AUTH_SESSION_TTL_MINUTES * 60,
        expires=settings.AUTH_SESSION_TTL_MINUTES * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear auth cookie on logout."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def _create_auth_session(
    *,
    db: Session,
    user: User,
    request: Request,
    response: Response,
) -> dict[str, object]:
    """Create DB session row and set browser cookie."""
    token = generate_session_token()
    db_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=get_session_expiry(),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(db_session)
    db.commit()
    _set_auth_cookie(response, token)
    return {
        "authenticated": True,
        "user": _serialize_user(user),
    }


@router.get("/status")
def get_auth_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """Return auth state and first-run setup requirement."""
    user_count = _get_active_user_count(db)
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    user_payload = None

    if token:
        session = db.scalar(
            select(AuthSession)
            .join(User)
            .where(
                AuthSession.token_hash == hash_session_token(token),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > datetime.utcnow(),
                User.is_active.is_(True),
            )
        )
        if session:
            user_payload = _serialize_user(session.user)

    return {
        "authenticated": user_payload is not None,
        "requires_setup": user_count == 0,
        "user": user_payload,
    }


@router.post("/setup", status_code=status.HTTP_201_CREATED)
def setup_first_user(
    payload: SetupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Allow only first account bootstrap when no users exist."""
    auth_rate_limiter.hit(f"setup:{request.client.host if request.client else 'unknown'}")

    existing_users = _get_active_user_count(db)
    if existing_users > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="İlk kurulum tamamlanmış. Lütfen giriş yapın.",
        )

    email = normalize_email(payload.email)
    validate_password_strength(payload.password)

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "Hesabınız oluşturuldu. Şimdi giriş yapabilirsiniz.",
        "user": _serialize_user(user),
    }


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate user and rotate server-side session."""
    email = normalize_email(payload.email)
    rate_limit_key = f"login:{email}:{request.client.host if request.client else 'unknown'}"
    auth_rate_limiter.hit(rate_limit_key)

    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz e-posta veya parola.",
        )

    return _create_auth_session(db=db, user=user, request=request, response=response)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Revoke active session and clear browser cookie."""
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if token:
        db_session = db.scalar(
            select(AuthSession).where(AuthSession.token_hash == hash_session_token(token))
        )
        if db_session and db_session.revoked_at is None:
            db_session.revoked_at = datetime.utcnow()
            db.commit()

    _clear_auth_cookie(response)
    return {"success": True}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user."""
    return {
        "authenticated": True,
        "user": _serialize_user(current_user),
    }


@router.patch("/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile details."""
    email = normalize_email(payload.email)
    existing_user = db.scalar(
        select(User).where(User.email == email, User.id != current_user.id)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta adresi zaten kullanılıyor.",
        )

    current_user.full_name = payload.full_name.strip()
    current_user.email = email
    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Profil bilgileri güncellendi.",
        "user": _serialize_user(current_user),
    }


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut parola yanlış.",
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni parola mevcut parola ile aynı olamaz.",
        )

    validate_password_strength(payload.new_password)
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {
        "success": True,
        "message": "Parolanız güncellendi.",
    }


@router.delete("/account")
def delete_account(
    payload: DeleteAccountRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete current user account."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hesabı silmek için parolanızı doğrulamanız gerekiyor.",
        )

    db.delete(current_user)
    db.commit()
    _clear_auth_cookie(response)

    return {
        "success": True,
        "message": "Hesabınız silindi.",
        "requires_setup": _get_active_user_count(db) == 0,
    }
