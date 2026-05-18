from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import load_yaml

try:
    import boto3  # type: ignore
except Exception:  # noqa: BLE001
    boto3 = None

try:
    from botocore.config import Config as BotoConfig  # type: ignore
except Exception:  # noqa: BLE001
    BotoConfig = None


ROOT = Path(__file__).resolve().parents[2]
MODEL_CONFIG_PATH = ROOT / "configs" / "models.yaml"
STRICT_JSON_MARKERS = (
    "return strict json only",
    "output must be valid json and nothing else",
    "return valid json and nothing else",
    "valid json and nothing else",
)
FENCED_JSON_TAIL_MARKERS = (
    "fenced json block",
    "```json block",
    "markdown spec followed by exactly one final fenced json block",
)


def load_runner_profiles(config_path: Path) -> List[Dict[str, Any]]:
    payload = load_yaml(config_path)
    runners = payload.get("runners")
    if not isinstance(runners, list):
        raise ValueError(f"runners must be a list in {config_path}")
    return runners


def load_model_registry(config_path: Path = MODEL_CONFIG_PATH) -> Dict[str, Dict[str, Any]]:
    payload = load_yaml(config_path)
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError(f"models must be a list in {config_path}")
    registry: Dict[str, Dict[str, Any]] = {}
    for item in models:
        if not isinstance(item, dict):
            continue
        model_id = str(item.get("model_id") or "").strip()
        if not model_id:
            continue
        registry[model_id] = dict(item)
    return registry


def resolve_model_spec(model: str | Dict[str, Any], registry: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    if registry is None:
        registry = load_model_registry()
    if isinstance(model, str):
        if model in registry:
            resolved = dict(registry[model])
            resolved.setdefault("model_id", model)
            return resolved
        return {"provider": "bedrock", "model_id": model}

    resolved = dict(model)
    model_id = str(resolved.get("model_id") or "").strip()
    merged = dict(registry.get(model_id, {})) if model_id else {}
    merged.update(resolved)
    if not merged.get("provider"):
        merged["provider"] = "bedrock"
    if not merged.get("model_id") and model_id:
        merged["model_id"] = model_id
    return merged


def get_bedrock_client(
    *,
    connect_timeout: Optional[int] = None,
    read_timeout: Optional[int] = None,
    max_attempts: Optional[int] = None,
) -> tuple[Any, str, Optional[str]]:
    if boto3 is None:
        raise RuntimeError("boto3 is required for Bedrock model calls")
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-2"
    profile = os.environ.get("AWS_PROFILE")
    session = boto3.Session(profile_name=profile, region_name=region)
    connect_timeout = int(connect_timeout or os.environ.get("EVAL_BEDROCK_CONNECT_TIMEOUT", "10"))
    read_timeout = int(read_timeout or os.environ.get("EVAL_BEDROCK_READ_TIMEOUT", "90"))
    max_attempts = int(max_attempts or os.environ.get("EVAL_BEDROCK_MAX_ATTEMPTS", "2"))
    client_kwargs: Dict[str, Any] = {}
    if BotoConfig is not None:
        client_kwargs["config"] = BotoConfig(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries={"max_attempts": max_attempts, "mode": "standard"},
        )
    return session.client("bedrock-runtime", **client_kwargs), region, profile


def call_bedrock_model(
    client: Any,
    model_id: str,
    system_text: str,
    user_text: str,
    max_tokens: int,
) -> Dict[str, Any]:
    if str(model_id).startswith("zai.glm-"):
        payload = {
            "messages": [
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
            "max_tokens": max_tokens,
            "temperature": 0,
        }
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json",
        )
        raw_body = response["body"].read().decode("utf-8")
        data = json.loads(raw_body)
        text = _extract_chat_text(data)
        usage = data.get("usage", {})
        choices = data.get("choices") or []
        finish_reason = None
        if choices and isinstance(choices[0], dict):
            finish_reason = choices[0].get("finish_reason")
        return {
            "text": text,
            "usage": usage,
            "stop_reason": finish_reason,
            "raw_response": data,
        }
    response = client.converse(
        modelId=model_id,
        system=[{"text": system_text}],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
    )
    content = response.get("output", {}).get("message", {}).get("content", [])
    text = "".join(item.get("text", "") for item in content if "text" in item).strip()
    return {
        "text": text,
        "usage": response.get("usage", {}),
        "stop_reason": response.get("stopReason"),
    }


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _request_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: Optional[int] = None) -> Dict[str, Any]:
    if timeout is None:
        timeout = int(os.environ.get("EVAL_HTTP_TIMEOUT", "120"))
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def _extract_chat_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        stripped = content.strip()
        if stripped:
            return stripped
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "output_text"} and item.get("text"):
                parts.append(str(item["text"]))
        joined = "".join(parts).strip()
        if joined:
            return joined
    return ""


def _is_deepseek_model(model_spec: Dict[str, Any]) -> bool:
    model_id = str(model_spec.get("model_id") or "").lower()
    api_model_name = str(model_spec.get("api_model_name") or "").lower()
    env = model_spec.get("env") or {}
    base_url = str(env.get("base_url") or "").lower()
    return "deepseek" in model_id or "deepseek" in api_model_name or "api.deepseek.com" in base_url


def _is_mimo_model(model_spec: Dict[str, Any]) -> bool:
    model_id = str(model_spec.get("model_id") or "").lower()
    api_model_name = str(model_spec.get("api_model_name") or "").lower()
    env = model_spec.get("env") or {}
    base_url = str(env.get("base_url") or "").lower()
    return "mimo" in model_id or "mimo" in api_model_name or "xiaomimimo.com" in base_url


def _usage_output_tokens(usage: Dict[str, Any]) -> int:
    for key in ("completion_tokens", "outputTokens", "completionTokens"):
        value = usage.get(key)
        if isinstance(value, int):
            return value
    return 0


def _retry_mimo_for_empty_visible_output(
    *,
    model_spec: Dict[str, Any],
    payload: Dict[str, Any],
    headers: Dict[str, str],
    url: str,
    max_tokens_field: str,
    original_max_tokens: int,
    finish_reason: Optional[str],
    usage: Dict[str, Any],
    text: str,
) -> Optional[Dict[str, Any]]:
    if not _is_mimo_model(model_spec):
        return None
    if text.strip():
        return None
    if finish_reason not in {"length", "repetition_truncation"}:
        return None
    if _usage_output_tokens(usage) < original_max_tokens:
        return None

    retry_payload = dict(payload)
    retry_payload[max_tokens_field] = min(max(original_max_tokens * 2, original_max_tokens + 800), 6000)
    retry_messages = list(retry_payload.get("messages") or [])
    if retry_messages and isinstance(retry_messages[0], dict):
        retry_messages[0] = dict(retry_messages[0])
        retry_messages[0]["content"] = (
            f"{retry_messages[0].get('content', '')}\n"
            "Answer directly and compactly. Keep the final visible response short."
        ).strip()
    retry_payload["messages"] = retry_messages
    retry_payload["temperature"] = 0
    return _request_json(url, retry_payload, headers)


def _retry_mimo_for_missing_fenced_tail(
    *,
    model_spec: Dict[str, Any],
    payload: Dict[str, Any],
    headers: Dict[str, str],
    url: str,
    max_tokens_field: str,
    original_max_tokens: int,
    finish_reason: Optional[str],
    usage: Dict[str, Any],
    text: str,
    system_text: str,
    user_text: str,
) -> Optional[Dict[str, Any]]:
    if not _is_mimo_model(model_spec):
        return None
    if not _expects_fenced_json_tail(system_text, user_text):
        return None
    if "```json" in text.lower():
        return None
    if finish_reason not in {"length", "repetition_truncation"}:
        return None
    if _usage_output_tokens(usage) < original_max_tokens:
        return None

    retry_payload = dict(payload)
    retry_payload[max_tokens_field] = min(max(original_max_tokens * 2, original_max_tokens + 1200), 7000)
    retry_messages = list(retry_payload.get("messages") or [])
    if retry_messages and isinstance(retry_messages[0], dict):
        retry_messages[0] = dict(retry_messages[0])
        retry_messages[0]["content"] = (
            f"{retry_messages[0].get('content', '')}\n"
            "Keep the narrative compact. Reserve enough output for the final fenced JSON block."
        ).strip()
    retry_payload["messages"] = retry_messages
    retry_payload["temperature"] = 0.2
    retry_payload["top_p"] = 0.95
    return _request_json(url, retry_payload, headers)


def _combined_prompt_text(system_text: str, user_text: str) -> str:
    return f"{system_text}\n{user_text}".lower()


def _expects_strict_json_output(system_text: str, user_text: str) -> bool:
    combined = _combined_prompt_text(system_text, user_text)
    if any(marker in combined for marker in FENCED_JSON_TAIL_MARKERS):
        return False
    return any(marker in combined for marker in STRICT_JSON_MARKERS)


def _expects_fenced_json_tail(system_text: str, user_text: str) -> bool:
    combined = _combined_prompt_text(system_text, user_text)
    return any(marker in combined for marker in FENCED_JSON_TAIL_MARKERS)


def _normalize_request_options(request_options: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(request_options)
    extra_body = normalized.pop("extra_body", None)
    if isinstance(extra_body, dict):
        normalized.update(extra_body)
    return normalized


def call_openai_compatible_chat(
    model_spec: Dict[str, Any],
    system_text: str,
    user_text: str,
    max_tokens: int,
    request_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    env = model_spec.get("env") or {}
    api_key_var = env.get("api_key_var")
    if not api_key_var:
        raise RuntimeError(f"api_key_var missing for model {model_spec.get('model_id')}")
    api_key = os.environ.get(str(api_key_var))
    if not api_key:
        raise RuntimeError(f"Missing required env var {api_key_var} for model {model_spec.get('model_id')}")

    base_url = env.get("base_url")
    if not base_url:
        base_url_var = env.get("base_url_var")
        if base_url_var:
            base_url = os.environ.get(str(base_url_var))
    if not base_url:
        raise RuntimeError(f"Missing base_url for model {model_spec.get('model_id')}")

    model_name = (
        env.get("model_name")
        or (os.environ.get(str(env.get("model_name_var"))) if env.get("model_name_var") else None)
        or model_spec.get("api_model_name")
        or model_spec.get("model_id")
    )
    if not model_name:
        raise RuntimeError(f"Missing api model name for model {model_spec.get('model_id')}")

    request_options = dict(model_spec.get("request_options") or {})
    if request_overrides:
        request_options = _deep_merge(request_options, request_overrides)
    request_options = _normalize_request_options(request_options)
    max_tokens_field = str(request_options.pop("max_tokens_field", "max_completion_tokens"))
    endpoint = str(request_options.pop("endpoint", "/chat/completions"))
    auth_header = str(request_options.pop("auth_header", "authorization")).lower()

    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
    }
    payload[max_tokens_field] = max_tokens
    payload.update(request_options)
    if _is_deepseek_model(model_spec):
        if _expects_strict_json_output(system_text, user_text):
            payload["response_format"] = {"type": "json_object"}
            payload["thinking"] = {"type": "disabled"}
            payload.pop("reasoning_effort", None)
            payload.setdefault("temperature", 0)
        elif _expects_fenced_json_tail(system_text, user_text):
            payload["thinking"] = {"type": "disabled"}
            payload.pop("reasoning_effort", None)
            payload.setdefault("temperature", 0)
        elif payload.get("thinking", {}).get("type") == "disabled":
            payload.pop("reasoning_effort", None)
    if payload.get("response_format") and not bool(model_spec.get("supports_json_mode", False)):
        payload.pop("response_format", None)
    if _is_mimo_model(model_spec):
        payload.pop("thinking", None)
        if _expects_strict_json_output(system_text, user_text):
            payload.setdefault("temperature", 0.2)
            payload.setdefault("top_p", 0.95)
        elif _expects_fenced_json_tail(system_text, user_text):
            payload.setdefault("temperature", 0.3)
            payload.setdefault("top_p", 0.95)

    url = urllib.parse.urljoin(_normalize_base_url(str(base_url)) + "/", endpoint.lstrip("/"))
    headers = {"Content-Type": "application/json"}
    if auth_header == "api-key":
        headers["api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    data = _request_json(
        url,
        payload,
        headers,
    )
    choices = data.get("choices") or []
    finish_reason = None
    if choices and isinstance(choices[0], dict):
        finish_reason = choices[0].get("finish_reason")
    usage = data.get("usage", {})
    text = _extract_chat_text(data)
    retry_data = _retry_mimo_for_empty_visible_output(
        model_spec=model_spec,
        payload=payload,
        headers=headers,
        url=url,
        max_tokens_field=max_tokens_field,
        original_max_tokens=max_tokens,
        finish_reason=finish_reason,
        usage=usage,
        text=text,
    )
    if retry_data is None:
        retry_data = _retry_mimo_for_missing_fenced_tail(
            model_spec=model_spec,
            payload=payload,
            headers=headers,
            url=url,
            max_tokens_field=max_tokens_field,
            original_max_tokens=max_tokens,
            finish_reason=finish_reason,
            usage=usage,
            text=text,
            system_text=system_text,
            user_text=user_text,
        )
    retry_used = False
    if isinstance(retry_data, dict):
        data = retry_data
        choices = data.get("choices") or []
        finish_reason = None
        if choices and isinstance(choices[0], dict):
            finish_reason = choices[0].get("finish_reason")
        usage = data.get("usage", {})
        text = _extract_chat_text(data)
        retry_used = True
    return {
        "text": text,
        "usage": usage,
        "id": data.get("id"),
        "status": data.get("status"),
        "finish_reason": finish_reason,
        "output_tokens": _usage_output_tokens(usage),
        "retry_used": retry_used,
        "raw_response": data,
    }


def call_model(
    client: Any,
    model: str | Dict[str, Any],
    system_text: str,
    user_text: str,
    max_tokens: int,
    request_overrides: Optional[Dict[str, Any]] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    model_spec = resolve_model_spec(model)
    provider = str(model_spec.get("provider") or "bedrock")
    if provider == "bedrock":
        if client is None:
            raise RuntimeError(f"Bedrock client is required for model {model_spec.get('model_id')}")
        return call_bedrock_model(client, str(model_spec["model_id"]), system_text, user_text, max_tokens)
    if provider in {"openai_compatible", "openai-chat-compatible"}:
        if timeout_seconds is not None:
            os.environ["EVAL_HTTP_TIMEOUT"] = str(max(1, int(timeout_seconds)))
        return call_openai_compatible_chat(model_spec, system_text, user_text, max_tokens, request_overrides=request_overrides)
    raise RuntimeError(f"Unsupported runner provider {provider!r} for model {model_spec.get('model_id')}")


def call_openai_responses(model: str, system_text: str, user_text: str, max_tokens: int) -> Dict[str, Any]:
    key = os.environ["OPENAI_API_KEY"]
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_text}]},
        ],
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": "low"},
    }
    data = _request_json(
        "https://api.openai.com/v1/responses",
        payload,
        {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    text = data.get("output_text") or ""
    if not text:
        parts: List[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    parts.append(str(content["text"]))
        text = "".join(parts)
    return {
        "text": text.strip(),
        "usage": data.get("usage", {}),
        "id": data.get("id"),
        "status": data.get("status"),
    }
