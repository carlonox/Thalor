#!/usr/bin/env python3
"""
ask_expert.py - Consult expert panel via FreeLLMAPI (Fusion Mode)

Calls the Fusion endpoint of FreeLLMAPI, which launches a panel of models
in parallel and a judge synthesizes the best response.

Requirements:
- FreeLLMAPI router running with fusion model configured
- FREELLMAPI_BASE_URL environment variable set
- FREELLMAPI_API_KEY environment variable set (optional if router doesn't require auth)

Usage:
    python3 ask_expert.py "Your problem description with full context"
"""

import sys
import os
import time
import logging
from openai import OpenAI

# Configuration
FREELLMAPI_BASE_URL = os.getenv("FREELLMAPI_BASE_URL", "http://host.docker.internal:3000/v1")
FREELLMAPI_API_KEY = os.getenv("FREELLMAPI_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger("ask_expert")

# Initialize OpenAI client with FreeLLMAPI endpoint
client = OpenAI(base_url=FREELLMAPI_BASE_URL, api_key=FREELLMAPI_API_KEY)

SYSTEM_PROMPT = """You are an expert panel in deep reasoning consulted by an AI agent when it's stuck on a problem it cannot solve. Your only function is to unblock it.

YOU WILL RECEIVE:
- The problem or deadlock where the agent is stuck
- The context the agent considered relevant

YOUR TASK (Synthesized by the judge from panel responses):
1. Reason step by step, without skipping assumptions. Verify each premise before building on it.
2. Explicitly identify where the trap is: false assumption? wrong approach? unconsidered edge case? hidden dependency?
3. Offer ONE concrete, actionable solution, or if not possible, a perspective shift that unblocks the agent.
4. If the solution requires code, deliver it minimal and verifiable.
5. If you detect the problem is poorly framed, say so and reframe it.

CONSTRAINTS:
- Don't ramble. Don't repeat the problem. Don't add "introduction" sections.
- If you don't know something with certainty, mark it as assumption, don't invent it.
- ALWAYS end with a single line:
  ACTION: <one sentence with the concrete next step the agent must execute>"""


def ask(prompt: str) -> str:
    """
    Consult the expert panel with a context-rich prompt.
    
    Args:
        prompt: The problem description with full context (language, OS, paths, code snippets)
    
    Returns:
        Synthesized expert response with actionable solution
    """
    t0 = time.time()
    try:
        log.info("Consulting expert panel (Fusion)...")
        response = client.chat.completions.create(
            model="fusion",  # The magic happens here
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            timeout=300  # 5 minutes — fusion takes longer due to parallel consultation
        )
        answer = response.choices[0].message.content.strip()
        
        if not answer or "i cannot" in answer.lower():
            raise RuntimeError("Expert panel returned empty or invalid response")
        
        log.info("OK in %.1fs", time.time() - t0)
        return answer
    
    except Exception as e:
        log.error("Failed to consult expert panel: %s", e)
        return (
            f"[ERROR] The expert panel is not available at this time. Error: {e}\n"
            "ESCALATE TO USER: ask your operator to consult this question directly with another AI."
        )


def main():
    if len(sys.argv) < 2:
        print(
            '[ERROR] Usage: python3 ask_expert.py "<problem where you are stuck>"',
            file=sys.stderr
        )
        sys.exit(1)
    
    print(ask(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()
