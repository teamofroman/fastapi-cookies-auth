import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.requests import HTTPConnection
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
    SimpleUser,
)
from starlette.middleware.authentication import AuthenticationMiddleware

app = FastAPI()


class MyUser(SimpleUser):
    def __init__(self, username: str) -> None:
        super().__init__(username)

    @property
    def is_admin(self):
        return self.username == 'this is user 123'


class MyAuthBackEnd(AuthenticationBackend):
    async def authenticate(
        self,
        conn: HTTPConnection,
    ) -> tuple[AuthCredentials, BaseUser] | None:
        token = conn.cookies.get('access_token', None)
        if token is None:
            return AuthCredentials(), None
        # TODO: Реализовать получение пользователя по токену
        user = f'this is user {token}'

        # TODO: Вместо MyUser возвращать нашего пользователя
        return AuthCredentials(['authenticated']), MyUser(user)


app.add_middleware(AuthenticationMiddleware, backend=MyAuthBackEnd())


async def get_current_user(request: Request):
    if not request.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='UNAUTHORIZED',
        )
    return request.user


async def get_current_user_admin(user: MyUser = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='FORBIDDEN',
        )
    return user


@app.post('/login/')
async def login(response: Response, username: str, passwd: str):
    if passwd != 'qwerty':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='UNAUTHORIZED',
        )
    response.set_cookie('access_token', username)
    return {'token': username}


@app.post('/logout/', dependencies=[Depends(get_current_user)])
async def logout(response: Response):
    response.delete_cookie('access_token')
    return {'token': 'unset'}


@app.get('/items/', dependencies=[Depends(get_current_user_admin)])
async def read_items(user: MyUser = Depends(get_current_user)):
    return {'user': user.display_name}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
