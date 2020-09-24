from typing import Dict, List, Tuple


def parse_args(args, valids: Dict[str, bool]) -> Tuple[Dict[str, str], List[str]]:
    valid_fields = {}
    bad_fields = []
    for arg in args:
        try:
            name, value = arg.split('=')
        except ValueError:
            continue
        if valids and name not in valids:
            bad_fields.append(name)
            continue
        if valids and valids[name]:
            valid_fields[name] = valid_fields.get(name, []) + [value] if value else []
        else:
            valid_fields[name] = value if value else None
    return valid_fields, bad_fields
