from fastapi import APIRouter

from app.api.v1 import appointments, auth, catalog, doctors, others, patients, schedules

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(doctors.router)
api_router.include_router(catalog.specialties_router)
api_router.include_router(catalog.services_router)
api_router.include_router(schedules.router)
api_router.include_router(appointments.router)
api_router.include_router(others.consultations_router)
api_router.include_router(others.authorizations_router)
api_router.include_router(others.notifications_router)
api_router.include_router(others.dashboard_router)
api_router.include_router(others.users_router)
api_router.include_router(others.audit_router)
