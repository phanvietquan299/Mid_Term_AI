BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
PURPLE = (128, 0, 128)
LIGHT_GREEN = (144, 238, 144)
DARK_GRAY = (30, 30, 30)
CYAN = (0, 255, 255)

MAX_SCREEN_WIDTH = 1800
MAX_SCREEN_HEIGHT = 1100
INFO_HEIGHT = 260
BUTTON_HEIGHT = 40

MANUAL_STEP_DELAY = 15  
AUTO_STEP_DELAY = 10
GAME_OVER_TIMER = 180
ROTATION_FLASH_DURATION = 30
PIE_FLASH_DURATION = 20
MESSAGE_DURATION = 90

HEURISTICS = [
    ("Auto", "auto"),
    ("ExactMST (H1)", "exact-mst"),
    ("Combined", "combo"),
    ("ExactDist", "exact-dist"),
    ("FoodMST", "mst"),
    ("PieAware", "pie")
]

KEY_TO_ACTION = {
    'up': "Up",
    'down': "Down", 
    'left': "Left",
    'right': "Right",
    'w': "Up",
    's': "Down",
    'a': "Left",
    'd': "Right",
    'space': "Stop"
}

ACTION_DELTAS = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
    "Stop": (0, 0)
}

DIRECTION_MAP = {
    "Up": "up",
    "Down": "down",
    "Left": "left",
    "Right": "right"
}
