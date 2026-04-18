# Testing, Formatting & Logging Best Practices

## Python Linter & Formatter Standards
To maintain high code quality across the team, adhere to the following best practices:
- **`ruff`**: Use `ruff` as the primary fast linter and standard ruleset enforcer to replace `flake8`/`isort`. Ensure imports are automatically sorted and unused variables are cleaned.
- **`black`**: Format all codebase files tightly to an 88-character line width margin using `black`. This ensures a uniform style and reduces diff syntax overhead.
- **`mypy`**: Utilize strict type hinting. Any data passing between FastAPI endpoints, PyTorch datasets, and gRPC routers must have explicitly declared types verifyable by `mypy`. Avoid relying on `Any`.

## Logging
- Standard `print()` statements are prohibited in production branches. 
- Rely on Python's built-in `logging` setup using a standardized schema.
- Because of the distributed nature of this gateway, utilize unique Trace IDs / `Job_ID` in the logs so they can easily be searched globally across log aggregators.
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info(f"[{job_id}] Started PGD loop step {step}")
  ```

## Testing
- **`pytest`** is the standard test runner.
- Write explicit unit tests testing isolated PyTorch operations (checking tensor dimensions and gradient flows) without requiring full surrogate network instantiation.
- Use `@pytest.mark.asyncio` for all asynchronous FastAPI and gRPC tests. Use `httpx` for standard `FastAPI` integration testing.
