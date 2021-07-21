from fastapi_users import FastAPIUsers

from backend.database import user_db, cookie_authentication, User, UserCreate, UserUpdate, UserDB

fastapi_users = FastAPIUsers(
    user_db,
    [cookie_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)