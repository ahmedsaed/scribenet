"""
Ollama LLM Client

Provides an HTTP-based client for interacting with Ollama API.
Supports both streaming and non-streaming generation with context management.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

# A very small, local print-based tracing strategy is used per user request


@dataclass
class OllamaResponse:
    """Response from Ollama API"""
    text: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class OllamaClient:
    """
    Async HTTP client for Ollama API
    
    Supports:
    - Text generation with /api/generate
    - Chat completion with /api/chat
    - Health checks with /api/tags
    - Context management
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        max_retries: int = 3,
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Base URL for Ollama server (default: http://localhost:11434)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def health_check(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model.get("name") for model in data.get("models", [])]
                    print(f"Ollama server healthy. Available models: {models}")
                    return True
                else:
                    print(f"Ollama health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"Ollama health check error: {e}")
            return False

    
    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        top_k: int = 40,
        context: Optional[List[int]] = None,
        stream: bool = False,
        **kwargs
    ) -> OllamaResponse:
        """
        Generate text using Ollama /api/generate endpoint
        
        Args:
            model: Model name (e.g., "llama3.1:8b")
            prompt: Input prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            context: Optional context from previous generation
            stream: Whether to stream response (not implemented yet)
            **kwargs: Additional Ollama parameters
        
        Returns:
            OllamaResponse with generated text
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # Non-streaming for now
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if context:
            payload["context"] = context
        
        # Add any additional kwargs to options
        payload["options"].update(kwargs)
        
        # If streaming is requested or a global token callback is set, use the streaming path
        if stream or _token_callback is not None:
            return await self._generate_stream(payload)

        for attempt in range(self.max_retries):
            try:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return OllamaResponse(
                            text=data.get("response", ""),
                            model=data.get("model", model),
                            done=data.get("done", True),
                            total_duration=data.get("total_duration"),
                            load_duration=data.get("load_duration"),
                            prompt_eval_count=data.get("prompt_eval_count"),
                            eval_count=data.get("eval_count"),
                        )
                    else:
                        error_text = await response.text()
                        print(f"Ollama generate failed: {response.status} - {error_text}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            raise Exception(f"Ollama generate failed after {self.max_retries} attempts")

            except aiohttp.ClientError as e:
                print(f"Ollama client error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    async def _generate_stream(self, payload: Dict[str, Any]) -> OllamaResponse:
        """Stream generation from Ollama and invoke the global token callback if present.

        Ollama returns JSON lines with response text chunks. We parse each line,
        extract the token/text, and pass it to the callback for live display.
        """
        import json
        
        session = await self._get_session()
        model = payload.get("model")
        full_text = ""

        try:
            # Set stream to true for Ollama
            payload["stream"] = True
            
            async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    print(f"Ollama stream start failed: {resp.status} - {txt}")
                    raise Exception("Ollama stream failed to start")

                # Read response line by line (Ollama sends newline-delimited JSON)
                async for line_bytes in resp.content:
                    try:
                        line = line_bytes.decode('utf-8').strip()
                    except Exception:
                        continue
                    
                    if not line:
                        continue
                    
                    try:
                        # Parse JSON response from Ollama
                        data = json.loads(line)
                        token = data.get("response", "")
                        
                        if token:
                            full_text += token
                            
                            # Send token to callback for live display
                            if _token_callback:
                                try:
                                    _token_callback(token)
                                except Exception:
                                    pass
                                    
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Ollama streaming error: {e}")

        return OllamaResponse(text=full_text, model=model or payload.get('model', ''), done=True)
    
    async def _chat_stream(self, payload: Dict[str, Any]) -> OllamaResponse:
        """Stream chat completion from Ollama."""
        import json
        
        session = await self._get_session()
        model = payload.get("model")
        full_text = ""

        try:
            # Set stream to true for Ollama
            payload["stream"] = True
            
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    print(f"Ollama chat stream failed: {resp.status} - {txt}")
                    raise Exception("Ollama chat stream failed to start")

                # Read response line by line (Ollama sends newline-delimited JSON)
                async for line_bytes in resp.content:
                    try:
                        line = line_bytes.decode('utf-8').strip()
                    except Exception:
                        continue
                    
                    if not line:
                        continue
                    
                    try:
                        # Parse JSON response from Ollama
                        data = json.loads(line)
                        message = data.get("message", {})
                        token = message.get("content", "")
                        
                        if token:
                            full_text += token
                            
                            # Send token to callback for live display
                            if _token_callback:
                                try:
                                    _token_callback(token)
                                except Exception:
                                    pass
                                    
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Ollama chat streaming error: {e}")

        return OllamaResponse(text=full_text, model=model or payload.get('model', ''), done=True)
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        top_k: int = 40,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> OllamaResponse:
        """
        Generate chat completion using Ollama /api/chat endpoint
        
        Args:
            model: Model name (e.g., "llama3.1:8b")
            messages: List of message dicts with "role" and "content"
                     Role can be "system", "user", or "assistant"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            stream: Whether to stream response (not implemented yet)
            tools: Optional list of tools for function calling
            **kwargs: Additional Ollama parameters
        
        Returns:
            OllamaResponse with generated text
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,  # Non-streaming for now
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            }
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional kwargs to options
        payload["options"].update(kwargs)
        
        # If streaming requested or global token callback is set, use streaming
        if stream or _token_callback is not None:
            return await self._chat_stream(payload)

        for attempt in range(self.max_retries):
            try:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract message content
                        message = data.get("message", {})
                        content = message.get("content", "")
                        tool_calls = message.get("tool_calls")

                        return OllamaResponse(
                            text=content,
                            model=data.get("model", model),
                            done=data.get("done", True),
                            total_duration=data.get("total_duration"),
                            load_duration=data.get("load_duration"),
                            prompt_eval_count=data.get("prompt_eval_count"),
                            eval_count=data.get("eval_count"),
                            tool_calls=tool_calls,
                        )
                    else:
                        error_text = await response.text()
                        print(f"Ollama chat failed: {response.status} - {error_text}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            raise Exception(f"Ollama chat failed after {self.max_retries} attempts")

            except aiohttp.ClientError as e:
                print(f"Ollama client error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models on Ollama server
        
        Returns:
            List of model information dictionaries
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                else:
                    print(f"Failed to list models: {response.status}")
                    return []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []


# Global client instance (singleton pattern)
_ollama_client: Optional[OllamaClient] = None
# Global callback to receive streaming tokens. Set by the UI (CLI) when a live
# spinner with token preview is desired. The callback should be a callable that
# accepts a single token (str).
_token_callback: Optional[Callable[[str], None]] = None


def set_token_callback(cb: Optional[Callable[[str], None]]):
    """Set a global token callback for streaming updates.

    Pass None to clear the callback.
    """
    global _token_callback
    _token_callback = cb


def get_ollama_client(
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> OllamaClient:
    """
    Get or create global Ollama client instance
    
    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds
    
    Returns:
        Shared OllamaClient instance
    """
    global _ollama_client
    
    if _ollama_client is None:
        _ollama_client = OllamaClient(base_url=base_url, timeout=timeout)
    
    return _ollama_client


async def close_ollama_client():
    """Close the global Ollama client"""
    global _ollama_client
    
    if _ollama_client:
        await _ollama_client.close()
        _ollama_client = None
