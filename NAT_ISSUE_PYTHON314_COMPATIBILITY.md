# TypeError: 'coroutine' object is not an async iterator - Python 3.14 Compatibility Issue

## Environment

- **nvidia-nat version**: 1.3.1
- **nvidia-nat-langchain version**: 1.3.1
- **Python version**: 3.14.0
- **Platform**: Linux x86_64 (NixOS)
- **Installation method**: uv + pyproject.toml

## Summary

When using `@register_function` decorator with Python 3.14, NAT's profiler wrapper causes a `TypeError: 'coroutine' object is not an async iterator` during function registration in `WorkflowBuilder.add_function()`. This prevents any registered functions/tools from initializing, breaking the entire workflow.

## Reproduction Steps

1. Create a custom tool/function using `@register_function` decorator:

```python
from nat.cli.register_workflow import register_function
from nat.builder.function_info import FunctionInfo
from nat.data_models.function import FunctionBaseConfig

class MyToolConfig(FunctionBaseConfig, name="my_tool"):
    pass

@register_function(config_type=MyToolConfig)
async def my_tool(config: MyToolConfig, builder):
    async def _single(input_data: str) -> str:
        return f"processed: {input_data}"
    
    return FunctionInfo.create(
        single_fn=_single,
        input_schema=str,
        single_output_schema=str,
        description="Test tool"
    )
```

2. Try to add function to builder:

```python
from nat.builder.workflow_builder import WorkflowBuilder

async with WorkflowBuilder() as builder:
    await builder.add_function("my_tool", MyToolConfig())
```

3. Error occurs during `builder.add_function()` call.

## Stack Trace

```
Traceback (most recent call last):
  File "/path/to/runtime_adapter.py", line 104, in _ensure_runtime
    await runtime.__aenter__()
  File "/path/to/runtime.py", line 37, in __aenter__
    await self.builder.add_function(name="tool_name", config=tool_config)
  File "/path/to/nat/builder/workflow_builder.py", line 476, in add_function
    build_result = await self._build_function(name=name, config=config)
  File "/path/to/nat/builder/workflow_builder.py", line 409, in _build_function
    build_result = await self._get_exit_stack().enter_async_context(build_fn(config, inner_builder))
  File "/nix/store/.../python3.14/contextlib.py", line 668, in enter_async_context
    result = await _enter(cm)
  File "/nix/store/.../python3.14/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
  File "/path/to/nat/profiler/decorators/framework_wrapper.py", line 135, in wrapper
    async with func(workflow_config, builder) as result:
  File "/nix/store/.../python3.14/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
  File "/path/to/nat/profiler/decorators/framework_wrapper.py", line 174, in base_fn
    async with original_build_fn(*args, **kwargs) as w:
  File "/nix/store/.../python3.14/contextlib.py", line 214, in __aenter__
    return await anext(self.gen)
TypeError: 'coroutine' object is not an async iterator
```

## Root Cause Analysis

The issue stems from **double async context manager wrapping** combined with **Python 3.14's changed behavior** for `asynccontextmanager`:

### Flow:

1. **Registration** (`nat/cli/register_workflow.py:170`):
   ```python
   def register_function_inner(fn: FunctionBuildCallableT[FunctionConfigT]):
       context_manager_fn = asynccontextmanager(fn)  # <-- First wrap
       # ...
       return context_manager_fn
   ```

2. **Profiler wrapping** (`nat/profiler/decorators/framework_wrapper.py:409`):
   ```python
   # In WorkflowBuilder._build_function:
   build_fn = chain_wrapped_build_fn(registration.build_fn, llms, function_frameworks)
   ```
   
   ```python
   # chain_wrapped_build_fn creates another async context manager:
   @asynccontextmanager
   async def base_fn(*args, **kwargs):
       async with original_build_fn(*args, **kwargs) as w:  # <-- Second wrap
           yield w
   ```

3. **Python 3.14 behavior change**: 
   - In Python 3.11/3.12, calling an `@asynccontextmanager`-decorated function returns an object that is directly usable with `async with`.
   - In Python 3.14, calling it returns a **coroutine** that needs to be awaited/iterated before it becomes an async context manager.
   - The profiler wrapper at line 174 tries: `async with original_build_fn(*args, **kwargs)` 
   - But `original_build_fn(*args, **kwargs)` returns a coroutine, not an async generator
   - Python 3.14's `contextlib.py` line 214 tries: `await anext(self.gen)` on a coroutine → TypeError

### Why This Happens:

The `asynccontextmanager` decorator in Python 3.14 changed its internal implementation. When a function decorated with `@asynccontextmanager` is called, the wrapper now returns a coroutine object rather than directly returning an object that implements the async context manager protocol.

## Workaround

Downgrade to Python 3.12 or 3.11:

```bash
# Using uv
uv python install 3.12
rm -rf .venv
unset UV_SYSTEM_PYTHON  # If set by shell environment
uv venv --python 3.12 .venv
uv sync
```

Update `pyproject.toml` to constrain Python version:

```toml
[project]
requires-python = ">=3.11,<3.14"
```

## Suggested Fix

The issue is in how NAT applies the profiler wrapper. Potential solutions:

### Option 1: Detect and skip redundant wrapping

In `nat/cli/register_workflow.py`, check if the function is already an async generator before applying `asynccontextmanager`:

```python
def register_function_inner(fn: FunctionBuildCallableT[FunctionConfigT]):
    from inspect import isasyncgenfunction
    
    # Only wrap if not already an async generator
    if isasyncgenfunction(fn):
        context_manager_fn = fn
    else:
        context_manager_fn = asynccontextmanager(fn)
    
    # ... rest of code
```

### Option 2: Fix profiler wrapper to handle Python 3.14

In `nat/profiler/decorators/framework_wrapper.py`, explicitly await/iterate the context manager:

```python
@asynccontextmanager
async def base_fn(*args, **kwargs):
    cm = original_build_fn(*args, **kwargs)
    # Ensure we have an async context manager, not a coroutine
    if inspect.iscoroutine(cm):
        cm = await cm
    async with cm as w:
        yield w
```

### Option 3: Pin Python < 3.14 in dependencies

Update NAT's `pyproject.toml`:

```toml
[project]
requires-python = ">=3.10,<3.14"
```

## Additional Context

- This affects ALL registered functions and tools, not just custom ones
- The error prevents runtime initialization entirely
- No workaround exists without downgrading Python
- Similar issues may exist with other `asynccontextmanager` usage in NAT

## Related Code Locations

- `src/nat/cli/register_workflow.py:170` - Initial asynccontextmanager wrap
- `src/nat/profiler/decorators/framework_wrapper.py:174` - Profiler wrapper async with call
- `src/nat/builder/workflow_builder.py:409` - Function build with profiler wrapper

## Version Information

```
nvidia-nat==1.3.1
nvidia-nat-langchain==1.3.1
Python 3.14.0
```

Working with Python 3.12.12 ✅
