from enum import Enum


class Day0Category(str, Enum):
    """
    Locked Day-0 Complaint Categories for UrbanPulse Platform.
    Strictly enforced across ingestion, categorization, and reporting.
    """
    road_damage = "road_damage"
    garbage_sanitation = "garbage_sanitation"
    streetlight_electrical = "streetlight_electrical"
    water_supply = "water_supply"
    drainage_flooding = "drainage_flooding"
    other = "other"


class UserRole(str, Enum):
    """
    Role-Based Access Control (RBAC) user roles.
    """
    Citizen = "Citizen"
    Admin = "Admin"
    Department = "Department"


class ReportStatus(str, Enum):
    """
    Lifecycle status for submitted citizen reports.
    Fault-tolerant ingestion defaults to received_pending_ai.
    """
    received_pending_ai = "received_pending_ai"
    processing = "processing"
    triaged = "triaged"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"
    duplicate_pending_review = "duplicate_pending_review"


class DataSource(str, Enum):
    """
    Provenance of report data. Ingestion defaults to user_submitted.
    """
    user_submitted = "user_submitted"
    sensor = "sensor"
    social_media = "social_media"
    manual_admin = "manual_admin"


class IncidentStatus(str, Enum):
    open = "open"
    triaged = "triaged"
    assigned = "assigned"
    investigating = "investigating"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IncidentPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
