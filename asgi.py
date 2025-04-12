from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import player_stats_routes, user_routes

app = FastAPI(
    title="Poker Bot API",
    description="Provides player data and statistics from the Telegram Poker Bot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_stats_routes.router)
app.include_router(user_routes.router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Hello!"}
