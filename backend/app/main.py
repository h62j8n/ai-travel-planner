from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.itinerary_service import GENERATION_FAILED_MESSAGE, GenerationError

app = FastAPI(title="AI Travel Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """입력 검증 실패 → §9 계약: {"error": "VALIDATION_ERROR", "message": ...}"""
    message = "입력값이 올바르지 않습니다."
    errors = exc.errors()
    if errors:
        raw = str(errors[0].get("msg", message))
        # 커스텀 validator의 "Value error, ..." 접두사를 제거해 사용자 메시지만 남긴다.
        message = raw.split("Value error, ")[-1]
    return JSONResponse(
        status_code=422,
        content={"error": "VALIDATION_ERROR", "message": message},
    )


@app.exception_handler(GenerationError)
async def generation_exception_handler(
    request: Request, exc: GenerationError
) -> JSONResponse:
    """AI 호출/파싱 실패 → §9 계약: {"error": "GENERATION_FAILED", "message": ...}"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "GENERATION_FAILED", "message": GENERATION_FAILED_MESSAGE},
    )
