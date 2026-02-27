from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import tasks, profile, shop

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Questly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(shop.router, prefix="/api")


@app.on_event("startup")
def startup():
    from seed import seed_defaults
    seed_defaults()
