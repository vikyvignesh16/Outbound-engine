import logging

from fastapi import FastAPI
from webhooks import clay_tam, clay_contacts, lemlist_events, albacross
from pipelines import qualification, enrichment, monthly_batch, daily_runner, content, contact_gaps, score_contacts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Brevo Outbound Engine")

app.include_router(clay_tam.router)
app.include_router(clay_contacts.router)
app.include_router(lemlist_events.router)
app.include_router(albacross.router)
app.include_router(qualification.router)
app.include_router(enrichment.router)
app.include_router(monthly_batch.router)
app.include_router(daily_runner.router)
app.include_router(content.router)
app.include_router(contact_gaps.router)
app.include_router(score_contacts.router)

@app.get("/health")
def health():
    return {"status": "ok"}
