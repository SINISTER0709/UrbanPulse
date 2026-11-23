"""
UrbanPulse Default Seed Script.
Seeds Day-0 initial users for each RBAC role (Citizen, Admin, Department)
and sample critical POIs (Schools, Hospitals, Transit Hubs) with spatial coordinates.
"""
import logging
from geoalchemy2.elements import WKTElement
from app.db.session import SessionLocal
from app.models.user import User
from app.models.poi import POI
from app.models.enums import UserRole
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

SEED_USERS = [
    {
        "email": "citizen@urbanpulse.local",
        "password": "CitizenPassword123!",
        "full_name": "Demo Citizen",
        "role": UserRole.Citizen
    },
    {
        "email": "admin@urbanpulse.local",
        "password": "AdminPassword123!",
        "full_name": "System Administrator",
        "role": UserRole.Admin
    },
    {
        "email": "department@urbanpulse.local",
        "password": "DeptPassword123!",
        "full_name": "Public Works Dept Lead",
        "role": UserRole.Department
    }
]

# Sensitive POIs for Location Risk (L) and proximity indexing
SEED_POIS = [
    {
        "name": "ABC Public School",
        "category": "school",
        "lat": 28.4506,
        "lng": 77.5842,
        "buffer_meters": 250.0,
        "data_source": "municipal_gis"
    },
    {
        "name": "City General Hospital",
        "category": "hospital",
        "lat": 28.6200,
        "lng": 77.2100,
        "buffer_meters": 300.0,
        "data_source": "municipal_gis"
    },
    {
        "name": "Central Metro Station",
        "category": "transit_hub",
        "lat": 28.6139,
        "lng": 77.2090,
        "buffer_meters": 200.0,
        "data_source": "osm_overpass"
    }
]


def seed():
    db = SessionLocal()
    try:
        # 1. Seed RBAC Users
        for u_data in SEED_USERS:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                user = User(
                    email=u_data["email"],
                    hashed_password=hash_password(u_data["password"]),
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    is_active=True
                )
                db.add(user)
                logger.info(f"Seeded user: {u_data['email']} ({u_data['role'].value})")
            else:
                logger.info(f"User already exists: {u_data['email']}")

        # 2. Seed POIs with spatial Point
        for poi_data in SEED_POIS:
            existing_poi = db.query(POI).filter(POI.name == poi_data["name"]).first()
            if not existing_poi:
                point_geom = WKTElement(f"POINT({poi_data['lng']} {poi_data['lat']})", srid=4326)
                poi = POI(
                    name=poi_data["name"],
                    category=poi_data["category"],
                    location=point_geom,
                    latitude=poi_data["lat"],
                    longitude=poi_data["lng"],
                    buffer_meters=poi_data["buffer_meters"],
                    data_source=poi_data["data_source"]
                )
                db.add(poi)
                logger.info(f"Seeded POI: {poi_data['name']} ({poi_data['category']})")
            else:
                logger.info(f"POI already exists: {poi_data['name']}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
