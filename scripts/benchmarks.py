import os, sys
from collections import OrderedDict

import benchmarkset
from executing import replace_placeholders_in_cmd_string

MODELS_DIR = "$BENCH_HOME/models"

PROPERTY_TYPES = OrderedDict()
PROPERTY_TYPES["rbr"] = "Reward-bounded reachability probability"
INSTANCES = benchmarkset.create_all_instances()
NAMES = list(dict.fromkeys([i["name"] for i in INSTANCES]).keys())

def get_full_model_filename(inst):
    return os.path.join(MODELS_DIR, inst["name"], inst["model"]["file"])
    return res

def get_full_property_filename(inst):
    return os.path.join(MODELS_DIR, inst["name"], inst["property"]["file"])

def from_id(identifier):
    for b in INSTANCES:
        if b["id"] == identifier: return b
    assert False, f"Instance with id {identifier} not found."

def check_instances():
    for inst in INSTANCES:
        modelfilename = replace_placeholders_in_cmd_string(get_full_model_filename(inst))
        assert os.path.isfile(modelfilename), f"Model file {modelfilename} does not exist."
        propfilename = replace_placeholders_in_cmd_string(get_full_property_filename(inst))
        assert os.path.isfile(propfilename), f"Property file {propfilename} does not exist."
        propname = inst["property"]["id"]
        with open(propfilename, 'r') as propfile:
            content = propfile.read()
        assert f'"{propname}":' in content, (f"Property file '{propfilename}' contents\n-----\n{content}\n-----\n...do not refer to property name {propname}. "
                                         f"Make sure to assign the property name like this:\n\t"
                                         f'"{propname}": Pmax=? ...')

if __name__ == "__main__":
    check_instances()
    print(f"Registered {len(NAMES)} benchmark models with {len(INSTANCES)} instances.")
    for name in NAMES:
        name_instances = [b for b in INSTANCES if b['name'] == name]
        print(f"Model '{name}' ({len(name_instances)} instances):\n\t" + "\n\t".join([b['id'] for b in name_instances]))
