import torch
from collections import OrderedDict


def rename_state_dict_keys(source, key_transformation, target=None):
    """
    source             -> Path to the saved state dict.
    key_transformation -> Function that accepts the old key names of the state
                          dict as the only argument and returns the new key name.
    target (optional)  -> Path at which the new state dict should be saved
                          (defaults to `source`)
    Example:
    Rename the key `layer.0.weight` `layer.1.weight` and keep the names of all
    other keys.
    ```py
    def key_transformation(old_key):
        if old_key == "layer.0.weight":
            return "layer.1.weight"
        return old_key
    rename_state_dict_keys(state_dict_path, key_transformation)
    ```
    """
    if target is None:
        target = source

    state_dict = torch.load(source)
    new_state_dict = OrderedDict()
    new_model_dict = OrderedDict()

    for key, value in state_dict.items():
        if key != "model":
            new_state_dict[key] = value

    for key, value in state_dict["model"].items():
        new_key = key_transformation(key)
        new_model_dict[new_key] = value

    new_state_dict["model"] = new_model_dict

    torch.save(new_state_dict, target)

def transform(old_key):
    print(old_key)
    if 'BatchNorm2d' in old_key or 'Conv2d' in old_key:
        num = old_key.split('.')[1]
        return old_key.replace('BatchNorm2d','batch_norm_'+str(num)).replace('Conv2d','conv_'+str(num))
    
    return old_key

rename_state_dict_keys("./yolov3new.pt", transform, './yolov3newtransformed.pt')
