"""
JSON schema validator for analysis output.
Ensures output matches expected structure and constraints.
"""

from typing import Dict, Any, List


def validate_tone(tone: str) -> bool:
    """Validate management tone value."""
    valid_tones = ["optimistic", "cautious", "neutral", "pessimistic"]
    return tone.lower() in valid_tones


def validate_confidence(confidence: str) -> bool:
    """Validate confidence level value."""
    valid_levels = ["high", "medium", "low"]
    return confidence.lower() in valid_levels


def validate_list_field(items: Any, min_items: int = 0, max_items: int = 10) -> bool:
    """Validate list fields."""
    if not isinstance(items, list):
        return False
    
    # Allow empty list or "Not mentioned"
    if len(items) == 0:
        return True
    
    # Check if it's a single "Not mentioned" string (converted to list)
    if len(items) == 1 and items[0] == "Not mentioned":
        return True
    
    # Validate length
    if not (min_items <= len(items) <= max_items):
        return False
    
    # All items must be strings
    return all(isinstance(item, str) for item in items)


def validate_forward_guidance(guidance: Any) -> bool:
    """Validate forward guidance structure."""
    if not isinstance(guidance, dict):
        return False
    
    required_keys = ["revenue", "margin", "capex"]
    if not all(key in guidance for key in required_keys):
        return False
    
    # All values must be strings
    return all(isinstance(guidance[key], str) for key in required_keys)


def validate_analysis_output(result: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate complete analysis output against schema.
    
    Args:
        result: Analysis result dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = [
        "management_tone",
        "confidence_level",
        "key_positives",
        "key_concerns",
        "forward_guidance",
        "capacity_utilization_trends",
        "growth_initiatives"
    ]
    
    for field in required_fields:
        if field not in result:
            return False, f"Missing required field: {field}"
    
    # Validate management_tone
    if not validate_tone(result["management_tone"]):
        return False, f"Invalid management_tone: {result['management_tone']}"
    
    # Validate confidence_level
    if not validate_confidence(result["confidence_level"]):
        return False, f"Invalid confidence_level: {result['confidence_level']}"
    
    # Validate list fields
    if not validate_list_field(result["key_positives"]):
        return False, "Invalid key_positives format"
    
    if not validate_list_field(result["key_concerns"]):
        return False, "Invalid key_concerns format"
    
    if not validate_list_field(result["growth_initiatives"]):
        return False, "Invalid growth_initiatives format"
    
    # Validate forward_guidance
    if not validate_forward_guidance(result["forward_guidance"]):
        return False, "Invalid forward_guidance structure"
    
    # Validate capacity_utilization_trends
    if not isinstance(result["capacity_utilization_trends"], str):
        return False, "capacity_utilization_trends must be a string"
    
    return True, "Valid"


def sanitize_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize output to ensure it matches schema.
    Convert edge cases to proper format.
    
    Args:
        result: Raw analysis result
        
    Returns:
        Sanitized result
    """
    # Ensure result is a dictionary
    if not isinstance(result, dict):
        raise ValueError(f"Expected dictionary, got {type(result).__name__}: {result}")
    
    sanitized = result.copy()
    
    # Ensure lists are actually lists
    for key in ["key_positives", "key_concerns", "growth_initiatives"]:
        if key in sanitized:
            if isinstance(sanitized[key], str):
                if sanitized[key].lower() == "not mentioned":
                    sanitized[key] = []
                else:
                    sanitized[key] = [sanitized[key]]
            elif not isinstance(sanitized[key], list):
                sanitized[key] = []
    
    # Ensure forward_guidance is a dict
    if "forward_guidance" in sanitized:
        if not isinstance(sanitized["forward_guidance"], dict):
            sanitized["forward_guidance"] = {
                "revenue": "Not mentioned",
                "margin": "Not mentioned",
                "capex": "Not mentioned"
            }
    
    # Ensure strings
    if "capacity_utilization_trends" in sanitized:
        if not isinstance(sanitized["capacity_utilization_trends"], str):
            sanitized["capacity_utilization_trends"] = "Not mentioned"
    
    if "management_tone" in sanitized:
        if not isinstance(sanitized["management_tone"], str):
            sanitized["management_tone"] = "neutral"
    
    if "confidence_level" in sanitized:
        if not isinstance(sanitized["confidence_level"], str):
            sanitized["confidence_level"] = "medium"
    
    return sanitized
