import os, json


def to_variable(name: str):
    return '${' + name + '}'

def substitute(template: str, replacers: dict):
    result = template
    for key in replacers:
        result = result.replace(to_variable(key), replacers[key])
    return result

template = open('sim_001_profile.template', 'r').read()
replacers = {
    'deviceId': '123456789',
    'tenantId': 't12345',
    'profileId': '7891011',
    'counter': '100'
}

print(substitute(template, replacers))

replacers["counter"] = "110"

print(substitute(template, replacers))