


def to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])