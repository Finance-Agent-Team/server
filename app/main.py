from fastapi import FastAPI

from .services import test_agent_activation

app = FastAPI()

@app.get("/test-activation")
async def test_activation_endpoint():
    result = await test_agent_activation()
    return {"success": result}