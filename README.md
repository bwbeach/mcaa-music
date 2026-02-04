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
