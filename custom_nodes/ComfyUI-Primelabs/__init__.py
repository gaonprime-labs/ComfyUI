from . import custom_s3
from . import custom_config

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    **custom_s3.NODE_CLASS_MAPPINGS,
    **custom_config.NODE_CLASS_MAPPINGS,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    **custom_s3.NODE_DISPLAY_NAME_MAPPINGS,
    **custom_config.NODE_DISPLAY_NAME_MAPPINGS,
}
