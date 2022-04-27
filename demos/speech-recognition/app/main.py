import logging
import os
import subprocess

import aiohttp
from aleph_client.vm.app import AlephApp
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)


http_app = FastAPI()
app = AlephApp(http_app=http_app)


def process_audio(audio_file: str):
    result = subprocess.run(
        [
            "deepspeech",
            "--model",
            "lib/deepspeech-0.9.3-models.pbmm",
            "--scorer",
            "lib/deepspeech-0.9.3-models.scorer",
            "--audio",
            audio_file,
        ],
        capture_output=True,
    )
    return result.stdout.strip()


@app.get("/")
async def index():
    return "Hello world"


@app.get("/ipfs/{ipfs_hash}")
async def process_audio_from_ipfs(ipfs_hash: str):
    ...


@app.get("/file/{file_path}")
async def process_audio_from_file(file_path: str):
    file_path = "lib/audio" + file_path
    return process_audio(file_path)


@app.get("/speech-to-text/aleph/{file_hash}")
async def process_audio_from_aleph_storage(file_hash: str):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        async with session.get(
            f"https://aleph.cloud/api/v0/storage/raw/{file_hash}"
        ) as response:
            if response.status != 200:
                response_text = await response.text()
                raise HTTPException(status_code=response.status, detail=response_text)

            audio_data = await response.read()

    tmp_dir = "/tmp"
    audio_file_path = os.path.join(tmp_dir, file_hash)

    with open(audio_file_path, "wb") as f:
        f.write(audio_data)

    try:
        result = process_audio(audio_file_path)
    finally:
        os.remove(audio_file_path)

    return result
