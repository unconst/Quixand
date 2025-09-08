from __future__ import annotations
import re
import os
import json
import time
import random
import aiohttp
import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple, Sequence, Literal, TypeVar, Awaitable
from fastapi import FastAPI

__version__: str = "0.0.0"

app = FastAPI(
    title="PROXY",
    description="Affine env proxy.",
)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

CHUTES_API_KEY = os.getenv("CHUTES_API_KEY", "")
if not CHUTES_API_KEY:
    print("Warning: CHUTES_API_KEY not set. Some features may not work.")
MODEL = 'GANGodfather/Affine-5ER7L69dC9dmuyJ5AT7HxeSYgKjAH5Y7FPy3BLJQmSBH7Zh3'
SLUG = 'gangodfather-gangodfather-affine-5er7l69dc9dmuyj5at7hxesyg'

@app.post("/env/chutes")
async def chutes(model: str, slug: str, prompt: str, timeout: float = 60) -> str:
    url = f"https://{slug}.chutes.ai/v1/chat/completions"
    hdr = {"Authorization": f"Bearer {os.environ.get('CHUTES_API_KEY', '')}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    conn = aiohttp.TCPConnector(
        limit=100, 
        limit_per_host=0,
        ttl_dns_cache=300,
        enable_cleanup_closed=True
    )
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(
        connector=conn,
        timeout=timeout_cfg
    ) as client:
        async with client.post(url, json=payload, headers=hdr) as r:
            return await r.json()
    
@app.post("/env/run")
async def run() -> dict:
    prompt = "1 + 1 = ?"          
    result = await chutes(model=MODEL, slug = SLUG, prompt=prompt)   
    response = result["choices"][0]["message"]["content"]
    score = 1.0 if response == "2" else 0.0 
    return {'prompt': prompt, 'response': response, 'score': score }

    
async def main():
    import quixand as qs
    docker_file = os.path.dirname(__file__) + "/"
    print(docker_file)
    sandbox = qs.Sandbox(
        template=qs.Templates.build(os.path.dirname(__file__) + "/", name="sat"),
        timeout=60,
        env={
            "CHUTES_API_KEY": CHUTES_API_KEY,
            "MODEL": MODEL,
            "SLUG": SLUG
        },
    )
    print('build docker')
    # Wait for server readiness
    max_retries = 30
    for i in range(max_retries):
        try:
            hc = sandbox.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/health"], timeout=5)
            if hc.text.strip() == "200":
                break
        except Exception:
            pass
        await asyncio.sleep(1)
            
    run_cmd = ( "curl -sS -X POST http://localhost:8000/env/run") 
    result = sandbox.run(run_cmd, timeout=60)
    print (result)

if __name__ == "__main__":
    asyncio.run(main())
