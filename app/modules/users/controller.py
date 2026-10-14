"""
Users controller: the business logic for users.

Controllers don't know about HTTP. They receive plain data, work with the
database and either return a result or raise one of our custom errors
(NotFoundError, ConflictError...), which are turned into HTTP responses
by the handler in `app/core/exceptions.py`.
"""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import paginate
from app.core.security import hash_password, verify_password
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import ChangePasswordRequest, UserAdminUpdate, UserFilters, UserUpdate


def check_admin(user: User) -> None:
    """
    Stop here with 403 unless the user is an admin.

    Every admin-only controller function calls this on its FIRST line,
    before touching the database.
    """
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")


def get_user_by_email(db: Session, email: str) -> User | None:
    # Emails are always stored in lowercase, so "John@Mail.com" == "john@mail.com"
    return db.scalar(select(User).where(User.email == email.lower()))


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    if data.email is not None and data.email.lower() != user.email:
        if get_user_by_email(db, data.email):
            raise ConflictError("Email is already registered")
        user.email = data.email.lower()
    if data.full_name is not None:
        user.full_name = data.full_name

    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: ChangePasswordRequest) -> None:
    if not verify_password(data.current_password, user.hashed_password):
        raise BadRequestError("Current password is incorrect")
    user.hashed_password = hash_password(data.new_password)
    db.commit()


# ---------- Admin only ----------


def list_users(db: Session, params: UserFilters, current_user: User) -> dict:
    check_admin(current_user)

    query = select(User).order_by(User.id)
    if params.search:
        pattern = f"%{params.search}%"
        query = query.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    if params.role:
        query = query.where(User.role == params.role)
    return paginate(db, query, params)


def get_user(db: Session, user_id: int, current_user: User) -> User:
    check_admin(current_user)

    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


def admin_update_user(db: Session, user_id: int, data: UserAdminUpdate, current_user: User) -> User:
    user = get_user(db, user_id, current_user)  # also checks that current_user is an admin
    if user.id == current_user.id:
        # Stops an admin from accidentally locking themselves out.
        raise BadRequestError("You cannot change your own role or status")

    # exclude_none=True -> only the fields the client actually sent
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
