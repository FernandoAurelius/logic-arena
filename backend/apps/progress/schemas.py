from ninja import Schema


class UserProgressSummarySchema(Schema):
    xp_total: int
    level: int
    xp_into_level: int
    xp_to_next_level: int

