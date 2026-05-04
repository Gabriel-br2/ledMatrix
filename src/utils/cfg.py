from typing import Any

from config.json import JsonConfigManager

DEFAULT_JSON_PAYLOAD: dict[str, Any] = {
    "screen": {
        "x_max": 64,
        "y_max": 32,
        "tam_pixel": 15,
        "tam_space": 5,
    },
    "main": {
        "path": "/home/gabriel/Documents/code/ledMatrix/",
    },
}

json_manager = JsonConfigManager("CONFIG/config.json", DEFAULT_JSON_PAYLOAD)
config = json_manager.load()
