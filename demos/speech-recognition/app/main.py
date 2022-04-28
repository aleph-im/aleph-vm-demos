import logging
import os
import subprocess

import aiohttp
from aleph_client.vm.app import AlephApp
from fastapi import FastAPI, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)

http_app = FastAPI()
app = AlephApp(http_app=http_app)


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


@app.get("/speech-to-text/aleph/{file_hash}")
async def process_audio_from_aleph_storage(file_hash: str):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        async with session.get(
            f"https://api2.aleph.im/api/v0/storage/raw/{file_hash}"
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
