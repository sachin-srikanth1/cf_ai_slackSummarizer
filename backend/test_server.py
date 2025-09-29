from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Test server is running", "timestamp": datetime.utcnow().isoformat()}

@app.get("/test")
async def test():
    return {"status": "success", "message": "All endpoints are working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_server:app", host="0.0.0.0", port=8000, reload=True)