import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from litestar import Controller, get
from litestar.exceptions import HTTPException, NotAuthorizedException

from app.core.jwt_auth import require_auth
from app.core.logging import debug, error, info, warn

load_dotenv()

IMG_URL = os.getenv("IMG_URL")
BASIC_INFO_URL = os.getenv("BASIC_INFO_URL")
SEM_RESULTS_URL = os.getenv("OVERALL_MARKS_SHEET")

missing = {
    "IMG_URL": IMG_URL,
    "BASIC_INFO_URL": BASIC_INFO_URL,
    "OVERALL_MARKS_SHEET": SEM_RESULTS_URL,
}
missing = [k for k, v in missing.items() if not v]
if missing:
    error(f"Missing environment variables: {missing}")
    raise RuntimeError(f"Missing environment variables: {missing}")


class StudentController(Controller):
    path = "/student"

    async def fetch_upstream(self, url: str):
        debug("Fetching upstream")

        try:
            async with httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(10.0, connect=3.0),
            ) as client:
                r = await client.get(url)
                r.raise_for_status()
                info("Successful upstream response")
                return r
        except httpx.RequestError as e:
            error(f"University service unreachable | Error: {str(e)}")
            raise HTTPException(503, "University service unreachable")
        except httpx.HTTPStatusError as e:
            warn(f"University service error: {e.response.status_code}")
            raise HTTPException(502, "University service error")

    @get("/me/info", dependencies={"user": require_auth})
    async def get_basic_info(self, user: Dict) -> Dict[str, Any]:
        try:
            roll_no = user.get("roll_no")
            if not roll_no:
                raise NotAuthorizedException("Invalid token")
            r = await self.fetch_upstream(BASIC_INFO_URL.format(roll_no=roll_no))  # pyright: ignore[reportOptionalMemberAccess]
            return r.json()
        except Exception as e:
            error(f"Error fetching basic info | Error: {str(e)}")
            raise HTTPException(500, str(e))

    @get("/me/results", dependencies={"user": require_auth})
    async def get_sem_results(self, user: Dict) -> Dict[str, Any]:
        roll_no = user.get("roll_no")
        r = await self.fetch_upstream(SEM_RESULTS_URL.format(roll_no=roll_no))  # pyright: ignore[reportOptionalMemberAccess]
        return r.json()
