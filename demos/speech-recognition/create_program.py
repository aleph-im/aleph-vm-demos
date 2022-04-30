import json
import logging
import os

from aleph_client.__main__ import _load_account
from aleph_client.conf import settings
from aleph_client.synchronous import create_program, create_store
from aleph_client.types import StorageEnum
from aleph_message.models.program import Encoding
from typer import echo

logger = logging.getLogger(__name__)


ENGLISH_MODELS_MESSAGE = "25a393222692c2f73489dc6710ae87605a96742ceef7b91de4d7ec34bb688d94"
ENGLISH_MODELS_IPFS = "QmdvXEDpTfhKGYCDMUucEp4vGYCbQUYfSM9zhQwdmTrfWi"

VENV_MESSAGE = "02b8b4644fe212ecc7f4abbe178dc31fa224b91a6e1a6b52f204d34ff4e1044b"
VENV_IPFS = "QmYbVJL8gea1v3h6pD1XPcAtrfTkXWY8C7ig2iUreEh1tE"

CHANNEL = "TEST-WORKSHOP"


def create_program_squashfs(path):
    logger.debug("Creating squashfs archive...")
    os.system(f"mksquashfs {path} {path}.squashfs -noappend")
    path = f"{path}.squashfs"
    assert os.path.isfile(path)
    return path


def upload_program(account, program_squashfs_path: str) -> str:
    with open(program_squashfs_path, "rb") as fd:
        logger.debug("Reading file")
        # TODO: Read in lazy mode instead of copying everything in memory
        file_content = fd.read()
        logger.debug("Uploading file")
        result = create_store(
            account=account,
            file_content=file_content,
            storage_engine=StorageEnum.storage,
            channel=CHANNEL,
            guess_mime_type=True,
            ref=None,
        )
        logger.debug("Upload finished")
        echo(f"{json.dumps(result, indent=4)}")
        program_ref = result["item_hash"]
    return program_ref


def main():
    app_directory = "./app"

    account = _load_account(None, None)

    program_squashfs_path = create_program_squashfs(app_directory)
    assert os.path.isfile(program_squashfs_path)

    program_ref = upload_program(account, program_squashfs_path)

    runtime = settings.DEFAULT_RUNTIME_ID

    volumes = [
        {
            "comment": "Deepspeech English Models",
            "mount": "/model",
            "ref": ENGLISH_MODELS_MESSAGE,
            "use_latest": True,
        },
        {
            "comment": "Deepspeech Virtual Environment",
            "mount": "/opt/packages",
            "ref": VENV_MESSAGE,
            "use_latest": True,
        },
    ]

    result = create_program(
        account=account,
        program_ref=program_ref,
        entrypoint="main:app",
        runtime=runtime,
        storage_engine=StorageEnum.storage,
        channel=CHANNEL,
        address=None,
        session=None,
        api_server=settings.API_HOST,
        memory=4000,
        vcpus=4,
        timeout_seconds=180,
        encoding=Encoding.squashfs,
        volumes=volumes,
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
