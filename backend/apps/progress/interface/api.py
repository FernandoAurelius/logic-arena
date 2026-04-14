from ninja import Header, Router

from apps.accounts.application.services import require_session
from apps.accounts.schemas import ErrorSchema
from apps.progress.application.services import build_user_progress_summary
from apps.progress.schemas import UserProgressSummarySchema


router = Router(tags=['progress'])


@router.get('/me', response={200: UserProgressSummarySchema, 401: ErrorSchema}, summary='Retorna o resumo de progresso do usuário autenticado.')
def get_my_progress(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    return 200, build_user_progress_summary(session.user)
