from dotenv import load_dotenv
from litestar import Litestar

from app.controller.auth import AuthController
from app.controller.student import StudentController
from app.core.logging import info

load_dotenv()

app = Litestar(
    route_handlers=[AuthController, StudentController],
    on_startup=[lambda: info("University Proxy API starting up...")],
    on_shutdown=[lambda: info("University Proxy API shutting down...")],
)
