"""
AI analyzer module using GitHub Models with strict hallucination prevention.
"""

import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import json
from typing import Dict, List, Any


# System prompt for hallucination prevention
SYSTEM_PROMPT = """You are a professional financial research analyst.

CRITICAL RULES:
1. Use ONLY information explicitly stated in the document.
2. Do NOT infer, guess, or use external knowledge.
3. If information is missing or unclear, return the value: "Not mentioned"
4. Do NOT add explanations, notes, or commentary.
5. Output MUST be valid JSON matching the provided schema.
6. Do NOT include markdown code blocks or any text outside the JSON object.

Any violation of these rules is unacceptable."""


def get_user_prompt(text: str) -> str:
    """
    Generate user prompt for AI API.
    
    Args:
        text: Extracted document text
        
    Returns:
        Formatted prompt string
    """
    return f"""Analyze the following earnings call transcript or management discussion.

Extract the information strictly based on the text.

Return the result in the following JSON schema:

{{
  "management_tone": "<optimistic|cautious|neutral|pessimistic>",
  "confidence_level": "<high|medium|low>",
  "key_positives": ["<item1>", "<item2>", ...],
  "key_concerns": ["<item1>", "<item2>", ...],
  "forward_guidance": {{
    "revenue": "<value or 'Not mentioned'>",
    "margin": "<value or 'Not mentioned'>",
    "capex": "<value or 'Not mentioned'>"
  }},
  "capacity_utilization_trends": "<value or 'Not mentioned'>",
  "growth_initiatives": ["<item1>", "<item2>", ...]
}}

Rules:
- If a value is not mentioned in the text, use "Not mentioned"
- Do NOT make up information
- Do NOT include any text outside the JSON object
- Do NOT use markdown code blocks

DOCUMENT TEXT:
---
{text}
---"""


def initialize_client(api_key: str) -> ChatCompletionsClient:
    """
    Initialize GitHub Models API client.
    
    Args:
        api_key: GitHub personal access token
        
    Returns:
        Configured ChatCompletionsClient instance
    """
    endpoint = "https://models.inference.ai.azure.com"
    
    # Ensure api_key is a clean string
    if not isinstance(api_key, str):
        raise ValueError(f"API key must be a string, got {type(api_key).__name__}: {repr(api_key)}")
    
    api_key = api_key.strip()
    
    if not api_key:
        raise ValueError("API key is empty after stripping")
    
    # Create client with AzureKeyCredential (standard method for GitHub Models)
    try:
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
        return client
    except Exception as e:
        raise Exception(f"Failed to initialize GitHub Models client: {type(e).__name__}: {str(e)}")


def analyze_chunk(client: ChatCompletionsClient, text: str) -> Dict[str, Any]:
    """
    Analyze a single text chunk using GitHub Models.
    
    Args:
        client: Configured ChatCompletionsClient
        text: Text chunk to analyze
        
    Returns:
        Parsed JSON response
        
    Raises:
        Exception: If analysis fails or JSON is invalid
    """
    response_text = ""
    try:
        prompt = get_user_prompt(text)
        
        # Use dictionary format for messages instead of SystemMessage/UserMessage
        response = client.complete(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more deterministic output
            top_p=0.9,
            model="gpt-4o"
        )
        
        # Extract text from response
        response_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Remove first line (```json or ```)
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            raise Exception(f"Expected dictionary, got {type(result).__name__}")
        
        return result
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text}")
    except Exception as e:
        raise Exception(f"AI API error: {str(e)}")


def merge_results(chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge results from multiple chunks conservatively.
    Prefer "Not mentioned" over conflicting or uncertain data.
    
    Args:
        chunk_results: List of analysis results from each chunk
        
    Returns:
        Merged result dictionary
    """
    if len(chunk_results) == 1:
        return chunk_results[0]
    
    merged = {
        "management_tone": "",
        "confidence_level": "",
        "key_positives": [],
        "key_concerns": [],
        "forward_guidance": {
            "revenue": "Not mentioned",
            "margin": "Not mentioned",
            "capex": "Not mentioned"
        },
        "capacity_utilization_trends": "Not mentioned",
        "growth_initiatives": []
    }
    
    # Merge tone (majority vote)
    tones = [r.get("management_tone", "") for r in chunk_results if r.get("management_tone") != "Not mentioned"]
    if tones:
        merged["management_tone"] = max(set(tones), key=tones.count)
    else:
        merged["management_tone"] = "neutral"
    
    # Merge confidence (majority vote)
    confidences = [r.get("confidence_level", "") for r in chunk_results if r.get("confidence_level") != "Not mentioned"]
    if confidences:
        merged["confidence_level"] = max(set(confidences), key=confidences.count)
    else:
        merged["confidence_level"] = "medium"
    
    # Merge lists (combine and deduplicate)
    for key in ["key_positives", "key_concerns", "growth_initiatives"]:
        items = []
        for result in chunk_results:
            chunk_items = result.get(key, [])
            if isinstance(chunk_items, list):
                for item in chunk_items:
                    if item and item != "Not mentioned" and item not in items:
                        items.append(item)
        merged[key] = items[:5]  # Keep top 5
    
    # Merge forward guidance (prefer specific values)
    for guidance_key in ["revenue", "margin", "capex"]:
        values = []
        for result in chunk_results:
            val = result.get("forward_guidance", {}).get(guidance_key, "Not mentioned")
            if val and val != "Not mentioned":
                values.append(val)
        
        if values:
            # Check for conflicts
            unique_values = list(set(values))
            if len(unique_values) == 1:
                merged["forward_guidance"][guidance_key] = unique_values[0]
            else:
                # Multiple different values - concatenate
                merged["forward_guidance"][guidance_key] = " | ".join(unique_values)
    
    # Merge capacity trends (concatenate unique values)
    trends = []
    for result in chunk_results:
        trend = result.get("capacity_utilization_trends", "Not mentioned")
        if trend and trend != "Not mentioned" and trend not in trends:
            trends.append(trend)
    
    if trends:
        merged["capacity_utilization_trends"] = " | ".join(trends)
    
    return merged


def analyze_document(api_key: str, text: str, chunks: List[str] = None) -> Dict[str, Any]:
    """
    Analyze entire document (with or without chunking).
    
    Args:
        api_key: GitHub personal access token
        text: Full document text (used if chunks is None)
        chunks: Pre-chunked text segments (optional)
        
    Returns:
        Analysis result dictionary
    """
    client = initialize_client(api_key)
    
    if chunks and len(chunks) > 1:
        # Multi-chunk analysis
        results = []
        for i, chunk in enumerate(chunks):
            print(f"Analyzing chunk {i+1}/{len(chunks)}...")
            result = analyze_chunk(client, chunk)
            results.append(result)
        
        # Merge results
        return merge_results(results)
    else:
        # Single document analysis
        text_to_analyze = chunks[0] if chunks else text
        return analyze_chunk(client, text_to_analyze)

def analyze_financial_document(api_key: str, text: str, prompt: str) -> Dict[str, Any]:
    """
    Extract financial data using custom prompt.
    
    Args:
        api_key: GitHub personal access token
        text: Full document text
        prompt: Custom extraction prompt
        
    Returns:
        Parsed JSON response
    """
    client = initialize_client(api_key)
    
    response_text = ""
    try:
        response = client.complete(
            messages=[
                {"role": "system", "content": "You are a financial data extraction specialist. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Very low for deterministic extraction
            top_p=0.9,
            model="gpt-4o"
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(response_text)
        
        if not isinstance(result, dict):
            raise Exception(f"Expected dictionary, got {type(result).__name__}")
        
        return result
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text}")
    except Exception as e:
        raise Exception(f"Financial extraction error: {str(e)}")