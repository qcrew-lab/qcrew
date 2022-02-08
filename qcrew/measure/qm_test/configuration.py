config = {
    "con1": {
        "type": "opx1",
        "digital_outputs": {
            1: {},
        },
    },
    "elements": {
        "switch": {
            "digitalInputs": {
                "digital_input1": {"port": ("con1", 1), "delay": 0, "buffer": 0}
            }
        },
    },
}
