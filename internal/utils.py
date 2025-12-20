
def set_cursor(shape: int):
    # shape: 0–6
    # 0 or 1 = blinking block
    # 2 = steady block
    # 3 = blinking underline
    # 4 = steady underline
    # 5 = blinking bar
    # 6 = steady bar
    if shape > 6 or shape < 0:
        return
    print(f"\x1b[{shape} q", end="", flush=True)
