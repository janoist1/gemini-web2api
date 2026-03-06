import os
import time
import asyncio
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from gemini_webapi import GeminiClient
import json

# --- ABSOLUTE headless fix: Stop Keychain & Support Pi ---
import sys
import gemini_webapi.utils as utils_pkg
import gemini_webapi.client as client_mod

# 1. Brutally replace the browser loader everywhere
def silent_dummy_loader(**kwargs):
    return {}

# We need to find the modules even if there are name collisions
# Patch load_browser_cookies
try:
    import gemini_webapi.utils.load_browser_cookies as load_mod
    load_mod.load_browser_cookies = silent_dummy_loader
except: pass

# 2. Get the original get_access_token function
# In this library, gemini_webapi.utils.get_access_token is often the function itself
if callable(utils_pkg.get_access_token):
    original_get_access_token = utils_pkg.get_access_token
else:
    import gemini_webapi.utils.get_access_token as token_mod
    original_get_access_token = token_mod.get_access_token

async def robust_get_access_token(base_cookies, **kwargs):
    try:
        # We call the ORIGINAL function, but since we patched load_browser_cookies,
        # it will NEVER trigger the Keychain.
        return await original_get_access_token(base_cookies, **kwargs)
    except Exception as e:
        print(f"\n[CRITICAL] Auth failed: {e}")
        print("This usually means your cookies in .env are expired.")
        print("On Raspberry Pi: Copy a fresh .env from your Mac.")
        print("On Mac: Run './gemini.py update' to refresh cookies.\n")
        raise

# 3. Apply the patch to all references
utils_pkg.get_access_token = robust_get_access_token
client_mod.get_access_token = robust_get_access_token

# Also try to patch the module internal if possible
token_module = sys.modules.get('gemini_webapi.utils.get_access_token')
if token_module:
    token_module.load_browser_cookies = silent_dummy_loader
    if not callable(token_module): # if it's the module, patch the attribute
        setattr(token_module, 'get_access_token', robust_get_access_token)

load_dotenv()

app = FastAPI(title="Local Gemini API Proxy", version="1.0.0")

# --- Configuration ---
SECURE_1PSID = os.getenv("GEMINI_SECURE_1PSID")
SECURE_1PSIDTS = os.getenv("GEMINI_SECURE_1PSIDTS")
SECURE_1PSIDCC = os.getenv("GEMINI_SECURE_1PSIDCC")
PORT = int(os.getenv("PORT", 8000))

if not SECURE_1PSID:
    print("Warning: GEMINI_SECURE_1PSID not found in environment variables.")

# --- Global Client ---
client: GeminiClient = None


# --- Pydantic Models for OpenAI API Compatibility ---
class Message(BaseModel):
    role: str
    content: Optional[Union[str, List[Dict[str, Any]]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "ignore"


def extract_tool_calls(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Looks for JSON blocks in the text that follow our ReAct format:
    { "action": "tool_name", "parameters": { ... } }
    """
    import re
    # Look for ```json ... ``` blocks
    json_blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not json_blocks:
        # Try finding raw JSON objects if no markdown blocks
        json_blocks = re.findall(r"(\{.*\"action\".*\"parameters\".*\})", text, re.DOTALL)

    tool_calls = []
    for block in json_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and "action" in data and "parameters" in data:
                tool_calls.append({
                    "index": len(tool_calls),
                    "id": f"call_{int(time.time())}_{len(tool_calls)}",
                    "type": "function",
                    "function": {
                        "name": data["action"],
                        "arguments": json.dumps(data["parameters"])
                    }
                })
        except:
            continue
    
    return tool_calls if tool_calls else None


class ChatCompletionRequest(BaseModel):
    model: str = "gemini-3.0-pro"
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None

    class Config:
        extra = "ignore"


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]


class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]


# --- Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    global client
    if SECURE_1PSID and SECURE_1PSIDTS:
        print("Using cookies from environment variables.")
        client = GeminiClient(SECURE_1PSID, SECURE_1PSIDTS, proxy=None)
        
        # Add additional cookies if present
        if SECURE_1PSIDCC:
            client.cookies.set("__Secure-1PSIDCC", SECURE_1PSIDCC, domain=".google.com")
            
    else:
        print("Error: Gemini cookies not found in environment.")
        print("Please run './gemini.py update' to extract cookies from Chrome and update your .env file.")
        print("Then restart the server.")
        os._exit(1)
        
    await client.init(timeout=120, auto_close=False, close_delay=300, auto_refresh=True)
    print("Gemini Client Initialized.")


# --- Helper Functions ---
def format_messages(messages: List[Message], tools: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Strategy:
    Concatenate previous messages into a "history" block in the prompt,
    and send the last user message as the actual message.
    """
    system_instruction = ""
    history_text = ""
    last_user_message = ""

    def extract_text(content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    texts.append(part.get("text", ""))
            return " ".join(texts)
        return str(content)

    for i, msg in enumerate(messages):
        content_text = extract_text(msg.content)
        if msg.role == "system":
            system_instruction += f"{content_text}\n"
        elif i == len(messages) - 1 and msg.role == "user":
            last_user_message = content_text
        else:
            role_name = "User" if msg.role == "user" else "Assistant"
            history_text += f"{role_name}: {content_text}\n"

    # Inject Tools if present (ReAct style)
    if tools:
        tools_desc = "\nAVAILABLE TOOLS:\n"
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                tools_desc += f"- {func.get('name')}: {func.get('description')}\n"
                tools_desc += f"  Parameters: {json.dumps(func.get('parameters'))}\n"
        
        system_instruction += f"\n{tools_desc}\n"
        system_instruction += "\nIf you need to use a tool, respond ONLY with a JSON block in the following format:\n"
        system_instruction += "```json\n{\n  \"action\": \"tool_name\",\n  \"parameters\": { ... }\n}\n```\n"

    final_prompt = ""
    if system_instruction:
        final_prompt += f"Background/Instructions:\n{system_instruction}\n"
    if history_text:
        final_prompt += f"Conversation History:\n{history_text}\n"

    final_prompt += f"\nUser: {last_user_message}\nAssistant:"

    return final_prompt


# --- Endpoints ---
@app.get("/v1/models")
async def list_models():
    """
    Returns the supported models in OpenAI format.
    """
    from gemini_webapi.constants import Model
    models = []
    # Simplified mapping for common models
    for m in Model:
        if m.model_name != "unspecified":
            models.append({"id": m.model_name, "object": "model", "created": 1677610602, "owned_by": "google"})
    
    # Add common aliases for better compatibility with tools like OpenClaw
    models.append({"id": "gemini", "object": "model", "created": 1677610602, "owned_by": "google"})
    
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    global client
    from gemini_webapi.constants import Model

    # 1. Map requested model to Gemini model
    target_model = Model.G_3_0_PRO # Default
    req_model_lower = request.model.lower()
    
    if "thinking" in req_model_lower:
        target_model = Model.G_3_0_FLASH_THINKING
    elif "flash" in req_model_lower:
        target_model = Model.G_3_0_FLASH
    elif "1.5" in req_model_lower:
        # Check for 1.5 variants if they exist in the Enum
        for m in Model:
            if "1.5" in m.model_name and ("pro" in req_model_lower or "flash" in req_model_lower):
                if ("pro" in m.model_name and "pro" in req_model_lower) or ("flash" in m.model_name and "flash" in req_model_lower):
                    target_model = m
                    break

    # Simple prompt construction
    prompt = format_messages(request.messages, tools=request.tools)
    
    # 2. Start a fresh chat session for this request with the target model
    chat = client.start_chat(model=target_model)

    request_id = f"chatcmpl-{int(time.time())}"
    created_time = int(time.time())

    if request.stream:

        async def stream_generator():
            full_text = ""
            try:
                # Initial chunk
                chunk_data = ChatCompletionChunk(
                    id=request_id,
                    created=created_time,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0, delta={"role": "assistant"}, finish_reason=None
                        )
                    ],
                )
                yield f"data: {chunk_data.json()}\n\n"

                async for chunk in chat.send_message_stream(prompt):
                    if chunk.text_delta:
                        full_text += chunk.text_delta
                        chunk_data = ChatCompletionChunk(
                            id=request_id,
                            created=created_time,
                            model=request.model,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta={"content": chunk.text_delta},
                                    finish_reason=None,
                                )
                            ],
                        )
                        yield f"data: {chunk_data.json()}\n\n"

                # Final chunk - check for tool calls in the accumulated text
                tool_calls = extract_tool_calls(full_text)
                finish_reason = "tool_calls" if tool_calls else "stop"
                
                chunk_data = ChatCompletionChunk(
                    id=request_id,
                    created=created_time,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0, 
                            delta={"tool_calls": tool_calls} if tool_calls else {}, 
                            finish_reason=finish_reason
                        )
                    ],
                )
                yield f"data: {chunk_data.json()}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                print(f"Error streaming response: {e}")
                # ... same error handling as before
                error_chunk = ChatCompletionChunk(
                    id=request_id,
                    created=created_time,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta={"content": f"\n[Error: {str(e)}]"},
                            finish_reason="stop",
                        )
                    ],
                )
                yield f"data: {error_chunk.json()}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    else:
        try:
            response = await chat.send_message(prompt)
            print(f"DEBUG Response: {response.text}")

            tool_calls = extract_tool_calls(response.text)
            finish_reason = "tool_calls" if tool_calls else "stop"

            return ChatCompletionResponse(
                id=request_id,
                created=created_time,
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=Message(role="assistant", content=response.text, tool_calls=tool_calls),
                        finish_reason=finish_reason,
                    )
                ],
                usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(response.text.split()), "total_tokens": len(prompt.split()) + len(response.text.split())}
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error processing request: {e}")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
