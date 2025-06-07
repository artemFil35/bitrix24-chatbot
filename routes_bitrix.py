from fastapi import APIRouter, Request
import httpx
import os
from openai_client import ask_chatgpt

router = APIRouter()

@router.post("/bitrix-handler")
async def handle_bitrix_event(request: Request):
    data = await request.json()
    if data.get("event") == "ONIMBOTMESSAGEADD":
        message = data["data"]["PARAMS"]["MESSAGE"]
        dialog_id = data["data"]["PARAMS"]["DIALOG_ID"]
        bot_id = data["data"]["BOT_ID"]

        answer = ask_chatgpt(message)

        payload = {
            "BOT_ID": bot_id,
            "DIALOG_ID": dialog_id,
            "CLIENT_ID": os.getenv("BITRIX_CLIENT_ID"),
            "MESSAGE": answer
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                os.getenv("BITRIX_WEBHOOK_URL") + "imbot.message.add.json",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

    return {"result": "ok"}
