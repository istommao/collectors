
import functools
from sanic.response import redirect


async def check_request_for_authorization_status(request):
    # setattr(request, 'user', user)
    sessionid = request.cookies.get('sessionid')
    if not sessionid:
        return False

    # with await request.app.redis as r:
    #     if await r.exists(sessionid):
    #         return True
    return True

    return False


def user_authorized():

    def decorator(f):

        @functools.wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = await check_request_for_authorization_status(request)

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return redirect('/login')

        return decorated_function

    return decorator
