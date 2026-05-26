from fastapi import FastAPI
from webhooks import clay_tam

app = FastAPI(title="Brevo Outbound Engine")

app.include_router(clay_tam.router)

@app.get("/health")
def health():
    return {"status": "ok"}
