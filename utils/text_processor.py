"""
Text processing module for chunking long documents.
Handles documents that exceed token limits for LLM processing.
"""

from typing import List


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.
    Rough approximation: 1 token ≈ 4 characters
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def chunk_text(text: str, max_tokens: int = 2500, overlap_tokens: int = 100) -> List[str]:
    """
    Split text into chunks with overlap to maintain context.
    
    Args:
        text: Input text to chunk
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Number of tokens to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Estimate characters per chunk
    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4
    
    # If text is short enough, return as single chunk
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    sentences = text.split('. ')
    
    current_chunk = ""
    for sentence in sentences:
        # Add period back
        sentence = sentence.strip() + '. '
        
        # Check if adding this sentence exceeds limit
        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap (last few sentences)
            overlap_text = current_chunk[-overlap_chars:] if len(current_chunk) > overlap_chars else current_chunk
            current_chunk = overlap_text + sentence
        else:
            current_chunk += sentence
    
    # Add remaining text
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def needs_chunking(text: str, max_tokens: int = 6000) -> bool:
    """
    Check if text needs to be chunked.
    
    Args:
        text: Input text
        max_tokens: Maximum tokens allowed (default 6000 for gpt-4o)
        
    Returns:
        True if chunking is needed
    """
    return estimate_tokens(text) > max_tokens
