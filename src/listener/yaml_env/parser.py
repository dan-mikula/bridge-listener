import os
import re
import yaml
from dotenv import dotenv_values


def parse_config(path=None, data=None, tag="$"):
    # pattern for global vars: look for ${word}
    pattern = re.compile(".*?\${(\w+)}.*?")
    loader = yaml.SafeLoader
    config = dotenv_values(".env")
    loader.add_implicit_resolver(tag, pattern, None)

    def constructor_env_variables(loader, node):
        value = loader.construct_scalar(node)
        match = pattern.findall(value)
        if match:
            full_value = value
            for g in match:
                full_value = full_value.replace(f"${{{g}}}", config[g])
            return full_value
        return value

    loader.add_constructor(tag, constructor_env_variables)

    if path:
        with open(path) as conf_data:
            return yaml.load(conf_data, Loader=loader)
    elif data:
        return yaml.load(data, Loader=loader)
    else:
        raise ValueError("Either a path or data should be defined as input")
