import os
from typing import Dict

import httpx
from dotenv import load_dotenv
from litestar import Controller, Request, post
from litestar.exceptions import HTTPException
from msgspec import Struct

from app.core.jwt_auth import generate_token
from app.core.logging import critical, error, info, warn

load_dotenv()

SIGN_URL = os.getenv("SIGN_URL")
EXAMCELL_DOMAIN = os.getenv("EXAMCELL_DOMAIN")
CHANGE_PASSWD_URL = os.getenv("CHANGE_PASSWD_URL")


class LoginRequest(Struct):
    username: str
    password: str


class TokenResponse(Struct):
    access_token: str
    token_type: str


class ChangPasswdReq(Struct):
    mail: str


class MessageResponse(Struct):
    message: str


if not SIGN_URL:
    critical("SIGN_URL environment variable is not set")
    raise RuntimeError("SIGN_URL environment variable is not set")

if not EXAMCELL_DOMAIN:
    critical("EXAMCELL_DOMAIN environment variable is not set")
    raise RuntimeError("EXAMCELL_DOMAIN environment variable is not set")


class AuthController(Controller):
    path = "/auth"

    sign_url = SIGN_URL
    change_passwd_url = CHANGE_PASSWD_URL
    examcell_domain = EXAMCELL_DOMAIN
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json, text/plain, */*",
        "origin": "https://academics.mrdu.edu.in",
        "referer": "https://academics.mrdu.edu.in/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36",
    }

    @post("/login")
    async def login(self, request: Request, data: LoginRequest) -> TokenResponse:
        client_ip = request.client.host if request.client else "unknown"
        info(f"Login attempt {data.username} IP={client_ip}")

        async with httpx.AsyncClient(timeout=5, verify=False) as client:
            resp = await client.post(
                self.sign_url,
                headers=self.headers,
                json={
                    "username": data.username,
                    "password": data.password,
                    "ipAddress": client_ip,
                    "module": "ExamCell",
                    "domain": self.examcell_domain,
                },
            )

        if resp.status_code != 200:
            warn("Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        payload = resp.json()
        token = generate_token(
            {
                "roll_no": payload["username"],
                "role": payload["roles"],
            }
        )

        return TokenResponse(
            access_token=token,
            token_type="Bearer",
        )

    @post("/change-passwd")
    async def change_password(self, req: ChangPasswdReq) -> MessageResponse:
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.post(
                    self.change_passwd_url,  # pyright: ignore[reportArgumentType]
                    headers=self.headers,
                    json={
                        "emailId": req.mail,
                    },
                )
                if resp.status_code == 200:
                    if resp.json().get("status"):
                        return MessageResponse(message=resp.json().get("message"))
                    else:
                        raise HTTPException(400, resp.json().get("message"))
                else:
                    raise HTTPException(resp.status_code, "Failed to change password")
        except httpx.RequestError as e:
            error(f"Password change service unreachable: {str(e)}")
            raise HTTPException(503, "Password change service unreachable")
