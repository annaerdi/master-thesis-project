import inspect
import typing
from typing import List, Optional

def function_to_schema(func) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
        typing.Any: "any" 
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        param_info = {}
        param_type_hint = param.annotation

        origin_type = typing.get_origin(param_type_hint)
        args_type = typing.get_args(param_type_hint)

        if origin_type is list or origin_type is List:
            param_info["type"] = "array"
            if args_type and args_type[0] in type_map:
                param_info["items"] = {"type": type_map[args_type[0]]}
            else:
                param_info["items"] = {"type": "string"} # Default for list items if not specified
        elif origin_type is Optional or (origin_type is typing.Union and type(None) in args_type):
            # Handle Optional[X] or Union[X, None]
            actual_type = args_type[0] if args_type[0] is not type(None) else args_type[1]
            param_info["type"] = type_map.get(actual_type, "string")
            param_info["nullable"] = True
        else:
            param_info["type"] = type_map.get(param_type_hint, "string")

        if param.default != inspect.Parameter.empty:
            param_info["default"] = param.default
        
        parameters[param.name] = param_info

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect.Parameter.empty
    ]
    
    docstring = inspect.getdoc(func) or ""

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": docstring,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }