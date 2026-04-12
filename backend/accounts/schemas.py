from datetime import datetime

from ninja import Schema


class ErrorSchema(Schema):
    message: str


class LoginInputSchema(Schema):
    nickname: str
    password: str


class UserSchema(Schema):
    id: int
    nickname: str
    created_at: datetime
    xp_total: int
    level: int
    xp_into_level: int
    xp_to_next_level: int


class LoginResponseSchema(Schema):
    token: str
    created: bool
    user: UserSchema
