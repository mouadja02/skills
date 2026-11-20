"""Parse evaluation command arguments without invoking a shell."""

import json
import shlex


def parse_eval_command(command: str) -> list[str]:
    """Accept a JSON argument array or a POSIX-quoted command line."""
    command = command.strip()
    if command.startswith("["):
        args = json.loads(command)
    else:
        # Reject unquoted shell syntax rather than silently treating it as args.
        # Quoted or escaped punctuation belongs to the argument itself.
        quote = None
        escaped = False
        for char in command:
            if escaped:
                escaped = False
            elif char == "\\" and quote != "'":
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char in ";<>|&()":
                raise ValueError("Put pipelines or redirects in a reviewed evaluator script")
        args = shlex.split(command, posix=True, comments=False)

    if not isinstance(args, list) or not args or not all(
        isinstance(arg, str) and "\0" not in arg for arg in args
    ) or not args[0]:
        raise ValueError("The evaluation command must name an executable and optional arguments")
    return args
