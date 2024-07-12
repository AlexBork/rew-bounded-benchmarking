from collections import OrderedDict

import itertools

def create_property_info(identifier : str,  file_name : str):
    """
    Creates a dictionary with the information of a property.
    @param identifier: The identifier of the property. The first three letters yield the type of the property.
                        The next three letters encode the optimization direction (min or max)
                        If the seventh character is numeric, it encodes the number of different reward assignments involved in reward bounds
    @param file_name: The name of the file containing the property
    """
    assert len(identifier) >= 3, f"Invalid identifier for property: {identifier}"
    info = OrderedDict()
    info["id"] = identifier
    info["file"] = file_name
    info["type"] = identifier[:3]
    info["dir"] = identifier[3:6]
    assert info["dir"] in ["min", "max"], f"Unknown optimization direction for property {info['dir']}"
    if len(identifier) >= 7 and identifier[6].isnumeric():
        assert info["type"] in ["rbr"], f"Unknown extra information for property type {info['type']}"
        info["num-bnd-rew-assignments"] = int(identifier[6])
    else:
        assert info["type"] not in ["rbr"], f"Missing extra information for property of type {info['type']}"
    return info

def create_parameter_assignment(parameter_names, parameter_value_list):
    if type(parameter_value_list) is not list:
        return create_parameter_assignment(parameter_names, [parameter_value_list])
    return OrderedDict(zip(parameter_names, parameter_value_list))


def get_parameter_zero_padding(par_values):
    max_lengths = [0] * len(par_values[0]) if len(par_values) > 0 else []
    for p in par_values:
        for i in range(len(p)):
            max_lengths[i] = max(max_lengths[i], len(str(p[i])))
    return max_lengths


def create_inst_ids(model_name, property_id, par_names = None, par_values_list = None):
    # instance IDs shall not include "_" or "."
    assert "_" not in model_name and "_" not in property_id, f"Invalid character '_' in model name or property id: {model_name}, {property_id}"
    if par_names is None:
        return [f"{model_name}_{property_id}_"]
    par_fill = get_parameter_zero_padding(par_values_list)

    create_par_string = lambda par_val: "-".join([f"{n}{v:0{f}}" for n,v,f in zip(par_names, par_val, par_fill)])
    result = [f"{model_name}_{property_id}_{create_par_string(p)}" for p in par_values_list]
    return result

def create_instance(inst_id, model_name, property_id, file_parameter_names = None, open_parameter_names = None, instance_par_values = None,  model_filename = None, property_filename = None):
    inst = OrderedDict()
    inst["id"] = inst_id
    inst["name"] = model_name
    inst["model"] = OrderedDict()
    if file_parameter_names is not None:
        inst["model"]["file-parameters"] = create_parameter_assignment(file_parameter_names, instance_par_values[:len(file_parameter_names)])
    if open_parameter_names is not None:
        inst["model"]["open-parameters"] = create_parameter_assignment(open_parameter_names, instance_par_values[-len(open_parameter_names):])
    inst["model"]["file"] = f"{model_name}.prism" if model_filename is None else model_filename
    inst["model"]["formalism"] = "prism"
    inst["model"]["type"] = "pomdp"
    inst["property"] = create_property_info(property_id, file_name=f"{model_name}.props" if property_filename is None else property_filename)
    return inst

def create_model_instances(model_name, property_id, file_parameter_names = [], open_parameter_names = [], par_values_list = None, model_filename = None, property_filename = None):
    par_names = file_parameter_names + open_parameter_names
    if len(par_names) == 0:
        assert par_values_list is None
        ids = create_inst_ids(model_name, property_id)
        assert len(ids) == 1
        return [create_instance(ids[0], model_name, property_id, model_filename=model_filename, property_filename=property_filename)]
    else:
        assert par_values_list is not None
        assert len(par_values_list) > 0
        assert len(par_names) == len(par_values_list[0])
        par_values_list = [p if type(p) is list else [p] for p in par_values_list] # ensure list of lists
        ids = create_inst_ids(model_name, property_id, par_names, par_values_list)
        assert len(par_values_list) == len(ids)
        return [create_instance(id, model_name, property_id, file_parameter_names, open_parameter_names, par_val, model_filename, property_filename) for id,par_val in zip(ids, par_values_list)]


def create_all_instances():
    instances = []

    name = "incline"
    file_parameters = ["MAP", "N"]
    open_parameters = ["B1", "B2"]
    B1_values = [15,20,25,30]
    B2_values = [10,12,15,17,20]
    for MAP, N in itertools.product([1,2],[5]):
        par_val_list = [[MAP, N, b1,0] for b1 in B1_values]
        instances += create_model_instances(name, "rbrmax1", file_parameters, open_parameters , par_val_list, model_filename=f"{name}-grid{MAP}.prism")
        par_val_list = [[MAP, N, b1,b2] for b1,b2 in itertools.product(B1_values, B2_values)]
        instances += create_model_instances(name, "rbrmax2", file_parameters, open_parameters, par_val_list, model_filename=f"{name}-grid{MAP}.prism")


    name = "obstacle"
    file_parameters = ["MAP", "N"]
    open_parameters = ["B1", "B2"]
    B1_values = [15,20,25,30]
    B2_values = [10,12,15,17,20]
    for MAP, N in itertools.product([1],[5]):
        par_val_list = [[MAP, N, b1,0] for b1 in B1_values]
        instances += create_model_instances(name, "rbrmax1", file_parameters, open_parameters , par_val_list, model_filename=f"{name}-grid{MAP}.prism")
        par_val_list = [[MAP, N, b1,b2] for b1,b2 in itertools.product(B1_values, B2_values)]
        instances += create_model_instances(name, "rbrmax2", file_parameters, open_parameters, par_val_list, model_filename=f"{name}-grid{MAP}.prism")

    name = "rover"
    instances += create_model_instances(name, "rbrmax3")

    name = "service"
    instances += create_model_instances(name, "rbrmax2")



    return instances
