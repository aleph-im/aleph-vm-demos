import logging
import os
import subprocess
import tempfile

import aiohttp
from fastapi import FastAPI, File, HTTPException, UploadFile
from aleph_message.models import ItemType

logger = logging.getLogger(__name__)

app = FastAPI()

ALEPH_API_SERVER = "https://api2.aleph.im"


def process_audio(audio_file: str):
    os.environ["PYTHONPATH"] = f"/opt/packages:{os.getenv('PYTHONPATH', default=None)}"
    result = subprocess.run(
        [
            "/opt/packages/bin/deepspeech",
            "--model",
            "/model/deepspeech-0.9.3-models.pbmm",
            "--scorer",
            "/model/deepspeech-0.9.3-models.scorer",
            "--audio",
            audio_file,
        ],
        capture_output=True,
    )
    return result.stdout.strip()


@app.post("/upload-audio-file")
async def upload_audio_file(file: UploadFile = File(...)):
    content = await file.read()
    with open(f"/tmp/{file.filename}", "wb") as f:
        f.write(content)


@app.get("/speech-to-text/file/{filename}")
async def process_audio_from_file(filename: str):
    file_path = os.path.join("/tmp", filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return process_audio(file_path)


async def get_file_from_storage(content_hash: str, content_type: ItemType) -> bytes:
    if content_type == ItemType.storage:
        uri = f"{ALEPH_API_SERVER}/api/v0/storage/raw/{content_hash}"
    elif content_type == ItemType.ipfs:
        uri = f"https://ipfs.io/ipfs/{content_hash}"
    else:
        raise ValueError(f"Unsupported item type: {content_type}")

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        async with session.get(uri) as response:
            if response.status != 200:
                response_text = await response.text()
                raise HTTPException(status_code=response.status, detail=response_text)

            return await response.read()


async def download_audio_from_aleph(message_hash: str) -> bytes:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        async with session.get(
            f"{ALEPH_API_SERVER}/api/v0/messages.json?hashes={message_hash}"
        ) as response:
            if response.status != 200:
                response_text = await response.text()
                raise HTTPException(status_code=response.status, detail=response_text)

            aleph_message = (await response.json())["messages"][0]

    content = aleph_message["content"]
    item_type = ItemType(content["item_type"])

    audio_data = await get_file_from_storage(content["item_hash"], item_type)
    return audio_data


@app.get("/speech-to-text/aleph/{message_hash}")
async def process_audio_from_aleph_storage(message_hash: str):
    audio_data: bytes = await download_audio_from_aleph(message_hash=message_hash)
    with tempfile.NamedTemporaryFile() as audio_file:
        audio_file.write(audio_data)
        audio_file.flush()
        return process_audio(audio_file.name)
