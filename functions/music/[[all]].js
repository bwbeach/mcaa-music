// Based on code here: https://developers.cloudflare.com/pages/tutorials/use-r2-as-static-asset-storage-for-pages/
export async function onRequestGet(ctx) {
  const path = new URL(ctx.request.url).pathname.replace("/music/", "");
  const file = await ctx.env.music.get(path);
  if (!file) return new Response(null, { status: 404 });
  return new Response(file.body, {
    headers: { "Content-Type": file.httpMetadata.contentType },
  });
}
