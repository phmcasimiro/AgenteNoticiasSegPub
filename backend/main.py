import os
import json
import hashlib
import redis
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Query
from dotenv import load_dotenv

from .models import NewsItem
from .database import init_db, save_to_db, search_db, get_recent_news_db
from .logging_config import setup_logging

# Load env variables
load_dotenv()

# Setup Logger
logger = setup_logging()

APP_TITLE = "Intelligence News Hub - Segurança Pública"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis Global State
redis_client = None
REDIS_AVAILABLE = False

# Initialize DB
# Initialize DB
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up Intelligence News Hub...")

    # Initialize Redis with Circuit Breaker
    global redis_client, REDIS_AVAILABLE
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        REDIS_AVAILABLE = True
        logger.info("✅ Redis Connected")
    except Exception as e:
        REDIS_AVAILABLE = False
        logger.warning(f"⚠️ Redis Connection Failed ({e}). Cache disabled.")

    # Start Scheduler
    scheduler.add_job(scheduled_fetch_job, CronTrigger(hour=11, minute=0))
    scheduler.add_job(scheduled_fetch_job, CronTrigger(hour=23, minute=0))
    scheduler.start()
    logger.info("⏰ Scheduler started (Jobs at 11:00 and 23:00)")

    yield
    # Shutdown logic if needed (e.g., scheduler.shutdown())


app = FastAPI(title=APP_TITLE, lifespan=lifespan)

# --- CORS Middleware (Required for Streamlit Cloud -> Render) ---
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua pelo domínio do Streamlit App
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security Middleware ---
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

APP_API_KEY = os.getenv("APP_API_KEY")
if not APP_API_KEY:
    logger.warning("⚠️ ADD_API_KEY not set! using insecure default for dev.")
    APP_API_KEY = "insecure_dev_key"


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    # Allow Health Check and Docs without Auth
    if request.url.path in ["/", "/docs", "/openapi.json", "/favicon.ico"]:
        return await call_next(request)

    # Check Header
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header != APP_API_KEY:
        logger.warning(f"⛔ Unauthorized access attempt from {request.client.host}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API Key"},
        )

    response = await call_next(request)
    return response


@app.get("/")
def health_check():
    return {"status": "ok", "service": APP_TITLE, "redis": REDIS_AVAILABLE}


@app.get("/news", response_model=List[NewsItem])
def get_news(q: str = Query(..., description="Termo de busca")):
    # 1. Cache (Redis) - Circuit Breaker
    cache_key = f"noticias:{q}"
    if REDIS_AVAILABLE and redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"Returning cached results for '{q}'")
                return [NewsItem(**item) for item in json.loads(cached)]
        except Exception as e:
            logger.error(f"Redis read error (Skipping): {e}")

    # 2. Database (SQLite)
    db_results = search_db(q)

    if db_results:
        logger.info(f"Found {len(db_results)} items in DB for '{q}'")
        return db_results

    # 3. External Search
    logger.info(f"External search for '{q}'")

    # Use shared fetcher logic to avoid duplication
    # We append "Distrito Federal" to ensure context, similar to previous logic
    items = fetcher.fetch_ddg(f"{q} Distrito Federal")

    if not items:
        logger.info(f"No results found via external search for '{q}'")

    # Save to DB and Cache
    if items:
        save_to_db(items)
        if REDIS_AVAILABLE and redis_client:
            try:
                redis_client.setex(
                    cache_key, 600, json.dumps([i.dict() for i in items], default=str)
                )
            except Exception as e:
                logger.warning(f"Failed to cache in Redis: {e}")

    return items


@app.get("/chat")
def chat_agent(q: str = Query(..., description="Pergunta para o Agente")):
    """
    Endpoint para conversar com o Agente de Segurança.
    """
    from .agent import get_agent_response

    response_text = get_agent_response(q)
    return {"response": response_text}


# --- Scheduler Implementation ---
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .fetchers import NewsFetcher

scheduler = AsyncIOScheduler()
fetcher = NewsFetcher()


async def scheduled_fetch_job():
    logger.info("⏰ Starting scheduled fetch job")
    try:
        import asyncio

        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, fetcher.fetch_all)

        if items:
            logger.info(f"✅ Scheduled: Fetched {len(items)} items. Saving...")
            save_to_db(items)
        else:
            logger.info("⚠️ Scheduled: No items found.")

    except Exception as e:
        logger.error(f"❌ Scheduled Job Failed: {e}")


@app.post("/force-fetch")
async def force_fetch_news():
    """Trigger news fetch immediately (Verification)"""
    await scheduled_fetch_job()
    return {"status": "Fetch triggered", "timestamp": datetime.now()}
