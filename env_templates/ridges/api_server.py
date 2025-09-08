import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from proxy.main import app as proxy_app
from proxy.main import lifespan as proxy_lifespan

from api.top.rank_1.agent import agent_main
from proxy.models import EmbeddingRequest, InferenceRequest, SandboxStatus
from proxy.chutes_client import ChutesClient
from proxy.providers import InferenceManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if not os.getenv("CHUTES_API_KEY") and os.getenv("CHUTES_API_KEY"):
    logger.warning("CHUTES_API_KEY is not set. Proxy endpoints may not work correctly.")

class AgentRequest(BaseModel):
    problem_statement: str = Field(default="", description="The problem statement to solve")
    run_id: Optional[str] = Field(default="default", description="Run ID for tracking")

app = FastAPI(
    title="Ridges Agent API",
    description="API wrapper for Ridges AI",
)

chutes_client = ChutesClient()  # For embeddings
inference_manager = InferenceManager()  # For inference


@app.post("/agents/embedding")
async def embedding_endpoint(request: EmbeddingRequest):
    try:
        logger.info(f"Embedding request input {request.input}")
        embedding_result = await chutes_client.embed(None, request.input)
        logger.info(f"Embedding request completed successfully")
        return embedding_result
    except HTTPException:
        raise
    except Exception as e:
        # More detailed error logging for debugging
        import traceback
        logger.error(f"Embedding request for run_id {request.run_id} -- error: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get embedding due to internal server error. Please try again later."
        )

@app.post("/agents/inference")
async def inference_endpoint(request: InferenceRequest):
    try:
        temperature = request.temperature if request.temperature is not None else DEFAULT_TEMPERATURE
        model = request.model if request.model is not None else DEFAULT_MODEL
        inference_result = await inference_manager.inference(
            run_id=None,
            messages=request.messages,
            temperature=temperature,
            model=model
        )
        try:
            if isinstance(inference_result, str):
                resp_preview = (inference_result[:200] + "…") if len(inference_result) > 200 else inference_result
            else:
                resp_preview = str(inference_result)[:200]
        except Exception:
            resp_preview = "<non-string response>"
        logger.info("Inference request completed successfully")
        return inference_result
    except HTTPException:
        logger.error(f"HTTPException in inference endpoint")
        raise
    except Exception as e:
        # More detailed error logging for debugging
        import traceback
        logger.error(f"Inference request for run_id {request.run_id} (model: {request.model}) -- error: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get inference due to internal server error. Please try again later."
        )

@app.get("/health")
async def health_check():
    return "OK"

@app.post("/agents/latest")
async def solve_problem(request: Optional[AgentRequest] = None):
    if request is None:
        request = AgentRequest(problem_statement="")

    try:
        problem_statement = request.problem_statement
        if not problem_statement:
            with open('problem_statement.txt', 'r', encoding='utf-8') as f:
                problem_statement = f.read().strip()
        agent_input = {
            "problem_statement": problem_statement,
        }
        loop = asyncio.get_running_loop()
    
        try:
            result = await loop.run_in_executor(None, agent_main, agent_input)
            output = {"success": True, "output": result}
        except Exception as e:
            logger.error(f"Exception during agent execution: {str(e)}", exc_info=True)
            error = traceback.format_exc()
            output = {"success": False, "error": error}
    except Exception as e:
        logger.error(f"Exception during agent execution: {str(e)}", exc_info=True)
        error = traceback.format_exc()
        output = {'success': False, 'error': error}

    with open('output.json', 'w') as f:
        json.dump(output, f)

    return output

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )