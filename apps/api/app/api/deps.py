from fastapi import Request


async def get_current_user(request: Request):
    return getattr(request.state, "user_id", None)
