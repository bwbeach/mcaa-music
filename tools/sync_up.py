#!/usr/bin/env -S uv run --script

import argparse
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


def main():
    parser = argparse.ArgumentParser(
        prog="sync_up.py",
        description="Upload files to R2, so they are available to stream",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Enable deletion of files in R2 that aren't in the local directory"
    )
    args = parser.parse_args()
        
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

    for key in sorted(remote):
        if key not in local:
            if args.delete:
                s3_client.delete_object(
                    Bucket=BUCKET_NAME,
                    Key=key,
                )
                print(f"deleted in R2: {key}")
            else:
                print(f"NOT DELETED: {key}")

    for key in sorted(local):
        if key not in remote:
            assert key.endswith(".mp3")
            with open(f"to_upload/{key}", "rb") as f:
                body = f.read()
            s3_client.put_object(
                Body=body,
                Bucket=BUCKET_NAME,
                ContentType="audio/mp3",
                Key=key,
            )
            print(f"uploaded: {key}")


if __name__ == "__main__":
    load_dotenv()
    main()

