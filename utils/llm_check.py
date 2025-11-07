"""
Utility to check if LLMs are working correctly.

This module provides functionality to test LLM connectivity and responses
using the Cerebras API via dspy.
"""

import os
import dspy
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

CEREBRAS_API_BASE = "https://api.cerebras.ai/v1"
CEREBRAS_MODEL = "openai/gpt-oss-120b"


def create_cerebras_lm(api_key: Optional[str] = None) -> Optional[dspy.LM]:
    """Create a dspy LM instance configured for Cerebras API."""
    if api_key is None:
        api_key = os.getenv("CEREBRAS_API_KEY")
    
    if not api_key:
        return None
    
    return dspy.LM(
        model=CEREBRAS_MODEL,
        api_key=api_key,
        api_base=CEREBRAS_API_BASE,
        max_tokens=200,
        temperature=0.7
    )


def check_llm_connection(
    api_key: Optional[str] = None,
    test_message: str = "Hello, this is a test message. Please respond with 'OK'."
) -> Optional[str]:
    """Check if the LLM is working by sending a test request using dspy."""
    lm = create_cerebras_lm(api_key)
    if lm is None:
        return None
    
    messages = [{"role": "user", "content": test_message}]
    response = lm.forward(messages=messages)
    
    # Extract response from chat completions
    return response.choices[0].message.content


def main():
    """Main function to run LLM check from command line."""
    test_message = "Tell me a short poem about coding."
    
    print("Checking LLM connection...")
    print(f"API Base: {CEREBRAS_API_BASE}")
    print(f"Model: {CEREBRAS_MODEL}")
    print("-" * 50)
    print(f"\nInput Message: {test_message}\n")
    
    response = check_llm_connection(test_message=test_message)
    
    if response:
        print("✓ LLM connection successful!")
        print(f"\nResponse:\n{response}")
    else:
        print("✗ LLM connection failed!")
    
    return response is not None


if __name__ == "__main__":
    exit(0 if main() else 1)
