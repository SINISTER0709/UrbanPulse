from enum import Enum
from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    road_damage = "road_damage"
    garbage_sanitation = "garbage_sanitation"
    streetlight_electrical = "streetlight_electrical"
    water_supply = "water_supply"
    drainage_flooding = "drainage_flooding"
    other = "other"


class AnalyzeCategoryRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)


class LLMCategoryOutput(BaseModel):
    category: CategoryEnum


class AnalyzeCategoryResponse(BaseModel):
    category: CategoryEnum
    department: str
    fallback_used: bool = False