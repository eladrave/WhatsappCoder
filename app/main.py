# app/main.py

from fastapi import FastAPI
from app.api.webhooks import router as webhook_router
from app.middleware.error_handler import add_exception_handlers

app = FastAPI(
    title="WhatsApp-AutoCoder Integration",
    description="An integration between WhatsApp and AutoCoder using LangChain and MCP.",
    version="0.1.0",
)

# Include routers
app.include_router(webhook_router, prefix="/webhook", tags=["webhooks"])

# Add exception handlers
add_exception_handlers(app)

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

