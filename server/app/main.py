from fastapi import FastAPI

app = FastAPI(
    title="quote-invoice-receipt generator API",
    version="1.0.0",
    description="generate quotes, invoices and receipts all in one place"
)

@app.get("/health")
async def health_check(): 
 return{
    "status": "ok"
}