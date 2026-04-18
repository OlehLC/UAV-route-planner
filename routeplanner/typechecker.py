import numbers
import numpy as np

SIGN_CHECK_MODES = [None, "neg", "non_neg", "non_pos", "pos"]
def __check_sign(value, value_name, sign_check=None):
    if sign_check not in SIGN_CHECK_MODES:
        raise ValueError(f"sign_check can be {SIGN_CHECK_MODES}, but it wasn't")
    
    if sign_check is None: return
    if sign_check == "neg" and value >= 0:
        raise ValueError(f"{value_name} must be negative")
    if sign_check == "non_neg" and value < 0:
        raise ValueError(f"{value_name} cannot be negative")
    if sign_check == "non_pos" and value > 0:
        raise ValueError(f"{value_name} cannot be positive")
    if sign_check == "pos" and value <= 0:
        raise ValueError(f"{value_name} must be positive")

def check_number(value, value_name, value_type, sign_check=None):
    if not isinstance(value, value_type):
        raise TypeError(f"{value_name} must be {value_type.__name__}")
    __check_sign(value, value_name, sign_check)


def check_onedim_ndarray_of_numbers(value, value_name, element_type, min_vals_count=0, sign_check=None):
    if not isinstance(value, np.ndarray):
        raise TypeError(f"{value_name} must be np.ndarray")
    if not np.issubdtype(value.dtype, element_type):
        raise TypeError(f"{value_name} must contain {element_type.__name__}")
    if value.ndim != 1:
        raise ValueError(f"{value_name} must have exactly one dimention")
    if len(value) < min_vals_count:
            raise ValueError(f"{value_name} must have at least {min_vals_count} values")
    
    if sign_check is None: return
    if sign_check == "neg" and value[value>=0].sum():
        raise ValueError(f"{value_name} must contain negative values")
    if sign_check == "non_neg" and value[value<0].sum():
        raise ValueError(f"{value_name} cannot contain negative values")
    if sign_check == "non_pos" and value[value>0].sum():
        raise ValueError(f"{value_name} cannot contain positive values")
    if sign_check == "pos" and value[value<=0].sum():
        raise ValueError(f"{value_name} must contain positive values")

def check_collection_of_numbers(value, value_name, collection_type, element_type, min_vals_count=0, sign_check=None):
    if not isinstance(value, collection_type):
        raise TypeError(f"{value_name} must be {collection_type.__name__}")
    if not all(isinstance(v, element_type)for v in value):
        raise TypeError(f"{value_name} must contain {element_type.__name__}")
    if len(value) < min_vals_count:
        raise ValueError(f"{value_name} must have at least {min_vals_count} values")
    
    if sign_check is None: return
    for el in value: 
        __check_sign(el, "values", sign_check)