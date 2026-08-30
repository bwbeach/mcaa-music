#!/usr/bin/env -S uv run --script

import boto3
import os

from dotenv import load_dotenv
from typing import Generator


BUCKET_NAME = "mcaa-music"


def local_files() -> Generator[str, None, None]:
    for root, dirs, files in os.walk("music"):
        prefix = root[6:]
        for f in files:
            yield f"{prefix}/{f}"


def remote_files(bucket) -> Generator[str, None, None]:
    for obj in bucket.objects.all():
        yield obj.key


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
    remote = set(remote_files(bucket))

    for key in remote:
        if key not in local:
            s3_client.delete_object(
                Bucket=BUCKET_NAME,
                Key=key,
            )
            print(f"deleted: {key}")

    for key in local:
        if key not in remote:
            response = s3_client.put_object(
                Body=f"music/{key}",
                Bucket=BUCKET_NAME,
                Key=key,
            )
            print(f"uploaded: {key}")


if __name__ == "__main__":
    load_dotenv()
    main()

