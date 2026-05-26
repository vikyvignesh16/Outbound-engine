from fastapi import FastAPI
from webhooks import clay_tam
from pipelines import qualification, enrichment

app = FastAPI(title="Brevo Outbound Engine")

app.include_router(clay_tam.router)
app.include_router(qualification.router)
app.include_router(enrichment.router)

@app.get("/health")
def health():
    return {"status": "ok"}
