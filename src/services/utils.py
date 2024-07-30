import json


async def get_key_by_args(*args, **kwargs) -> str:
    """Get key by args and kwargs."""
    return f'{args}:{json.dumps({"kwargs": kwargs}, sort_keys=True)}'
