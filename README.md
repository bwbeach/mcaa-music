# mcaa-music

Website to access practice recordings for the Maui Choral Arts Association.

## Setting up on Cloudflare

Cloudflare docs:

 - [Git Integration](https://developers.cloudflare.com/pages/get-started/git-integration/)
 - [Functions](https://developers.cloudflare.com/pages/functions/get-started/)

Updates:

 - Created `wrangler.jsonc` based on error message suggestion during deploy.
 - Set name in `wrangler.jsonc` to `mcaa-music`, as suggested by error message
 - Set assets dir to build output dir: `npx wrangler deploy --assets ./dist/`
 
### Setting up R2 Storage

#### R2

 - Turned on R2 storage for my account
 - Created a bucket called `mcaa-music` in the Western North America region.
 - Account id is: `fdd3cf56706534b30dee40ec7465bace`
 - Endpoint is: `https://fdd3cf56706534b30dee40ec7465bace.r2.cloudflarestorage.com` 
 
#### Cyberduck to upload files

 - "Open Connection" didn't work
 - creating a new bookmark did work, using the hostname, access key, and secret
 
#### Cloudflare

Add stanza to `wrangler.jsonc`:

```json
    "r2_buckets": [
        {
            "binding": "music",
            "bucket_name": "mcaa-music"
        }
    ]
```

