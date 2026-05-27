import logging

from fastapi import FastAPI
from webhooks import clay_tam
from pipelines import qualification, enrichment, monthly_batch, daily_runner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Brevo Outbound Engine")

app.include_router(clay_tam.router)
app.include_router(qualification.router)
app.include_router(enrichment.router)
app.include_router(monthly_batch.router)
app.include_router(daily_runner.router)

@app.get("/health")
def health():
    return {"status": "ok"}
