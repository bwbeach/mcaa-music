#!/usr/bin/env -S uv run --script

import os
from collections.abc import Generator

import boto3
from dotenv import load_dotenv

BUCKET_NAME = "mcaa-music"


def local_files() -> Generator[str, None, None]:
    for root, dirs, files in os.walk("to_upload"):
        yield from files


def remote_files(bucket) -> Generator[str, None, None]:
    for obj in bucket.objects.all():
        yield obj.key


def clean_key(k: str) -> str:
    """Removes all non-alpha-numeric characters from the string, except for the '.' in 'mp3'

    >>> clean_key("A B.C.mp3")
    'ABC.mp3'
    >>> clean_key("foo.bar.mp3")
    'foobar.mp3'
    """
    if not k.endswith(".mp3"):
        raise ValueError(f"keys must end with .mp3: {k}")
    return "".join(c for c in k[:-4] if c.isalnum()) + ".mp3"


def main():
    s3_client = boto3.client(
        service_name="s3",
        endpoint_url="https://fdd3cf56706534b30dee40ec7465bace.r2.cloudflarestorage.com",
        # region_name="auto",
    )
    s3_resource = boto3.resource(
        "s3",
        endpoint_url="https://fdd3cf56706534b30dee40ec7465bace.r2.cloudflarestorage.com",
    )
    bucket = s3_resource.Bucket("mcaa-music")

    local = set(local_files())
    clean_local = {clean_key(k) for k in local}
    remote = set(remote_files(bucket))

    for key in sorted(remote):
        break
        if key not in clean_local:
            s3_client.delete_object(
                Bucket=BUCKET_NAME,
                Key=key,
            )

    for key in sorted(local):
        if clean_key(key) not in remote:
            assert key.endswith(".mp3")
            with open(f"to_upload/{key}", "rb") as f:
                body = f.read()
            s3_client.put_object(
                Body=body,
                Bucket=BUCKET_NAME,
                ContentType="audio/mp3",
                Key=clean_key(key),
            )
            print(f"uploaded: {clean_key(key)}")


if __name__ == "__main__":
    load_dotenv()
    main()

