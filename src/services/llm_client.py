"""Claude LLM client wrapper with error handling and retry logic."""

import time
from typing import Optional

from anthropic import Anthropic, APIError, RateLimitError
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeLLMClient:
    """Wrapper for Anthropic Claude API with observability."""

    def __init__(self):
        """Initialize Claude client."""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.max_retries = 3
        self.retry_delay = 1.0

        logger.info("claude_client_initialized", model=self.model)

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> tuple[str, int]:
        """Generate response from Claude.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            
        Returns:
            Tuple of (response text, tokens used)
        """
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                # Prepare messages
                messages = [{"role": "user", "content": prompt}]

                # Call Claude API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else "",
                    messages=messages,
                )

                duration = time.time() - start_time

                # Extract response
                response_text = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens

                logger.info(
                    "claude_generation_success",
                    model=self.model,
                    tokens_used=tokens_used,
                    duration_seconds=round(duration, 3),
                    attempt=attempt + 1,
                )

                return response_text, tokens_used

            except RateLimitError as e:
                logger.warning(
                    "rate_limit_error",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise

            except APIError as e:
                logger.error(
                    "claude_api_error",
                    attempt=attempt + 1,
                    error=str(e),
                    exc_info=True,
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise

            except Exception as e:
                logger.error(
                    "claude_generation_error",
                    error=str(e),
                    exc_info=True,
                )
                raise

        # Should never reach here
        raise Exception("Max retries exceeded")

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4


# Global instance
llm_client = ClaudeLLMClient()
