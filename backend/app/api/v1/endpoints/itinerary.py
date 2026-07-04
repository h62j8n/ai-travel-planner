from fastapi import APIRouter

from app.schemas.itinerary import Itinerary, ItineraryRequest
from app.services.itinerary_service import generate_itinerary

router = APIRouter()


@router.post("", response_model=Itinerary)
async def create_itinerary(req: ItineraryRequest) -> Itinerary:
    # 검증 실패는 RequestValidationError, AI 실패는 GenerationError로
    # main.py의 예외 핸들러가 §9 계약 형태로 응답을 변환한다.
    return await generate_itinerary(req)
