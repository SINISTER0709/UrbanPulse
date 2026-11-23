from fastapi import APIRouter
from app.classifier import classify_complaint
from app.schemas import AnalyzeCategoryRequest, AnalyzeCategoryResponse

router = APIRouter(prefix="/api/analyze", tags=["LLM Classification"])


@router.post("/category", response_model=AnalyzeCategoryResponse)
def analyze_category(payload: AnalyzeCategoryRequest) -> AnalyzeCategoryResponse:
    return classify_complaint(payload.text)