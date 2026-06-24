from fastapi import APIRouter, Depends

from app.api.deps import DEFAULT_USER_ID, get_recommendation_service
from app.application.dtos.recommendation_dtos import RecommendationDTO
from app.application.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=RecommendationDTO)
async def get_recommendations(service: RecommendationService = Depends(get_recommendation_service)):
    return await service.get_recommendations(DEFAULT_USER_ID)
