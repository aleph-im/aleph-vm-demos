import logging
import os
import subprocess
import tempfile

import aiohttp
from fastapi import FastAPI, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)

app = FastAPI()


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


async def download_audio_from_aleph(file_hash) -> bytes:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        async with session.get(
            f"https://api2.aleph.im/api/v0/storage/raw/{file_hash}"
        ) as response:
            if response.status != 200:
                response_text = await response.text()
                raise HTTPException(status_code=response.status, detail=response_text)

            return await response.read()


@app.get("/speech-to-text/aleph/{file_hash}")
async def process_audio_from_aleph_storage(file_hash: str):
    audio_data: bytes = await download_audio_from_aleph(file_hash=file_hash)
    with tempfile.NamedTemporaryFile() as audio_file:
        audio_file.write(audio_data)
        audio_file.flush()
        return process_audio(audio_file.name)
