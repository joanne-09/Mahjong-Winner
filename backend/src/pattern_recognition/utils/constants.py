# Extract tile numbers and index
tile_numbers = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
words_index = ['east', 'south', 'west', 'north']

TILE_NAMES = [
    "blank",
    "b_one","b_two","b_three","b_four","b_five","b_six","b_seven","b_eight","b_nine",
    "s_one","s_two","s_three","s_four","s_five","s_six","s_seven","s_eight","s_nine",
    "w_one","w_two","w_three","w_four","w_five","w_six","w_seven","w_eight","w_nine",
    "east","south","west","north","zong","fa","bai",
    "spring","summer","autumn","winter","plum","orchid","chrysanthemum","bamboo",
]

DRAGON_NAMES = {"zong", "fa", "bai"}
DRAGON_ORDER = ("zong", "fa", "bai")
TRIPLET_TYPES = {"ke", "gang", "kong", "槓"}
SEASONS = {35, 36, 37, 38}
FLOWERS = {39, 40, 41, 42}
ALL_BONUS = SEASONS | FLOWERS

SUIT_LABELS = {
    "bing": "筒",
    "bamboo": "條",
    "wan": "萬",
}
WIND_LABELS = {
    "east": "東",
    "south": "南",
    "west": "西",
    "north": "北",
}
DRAGON_LABELS = {
    "zong": "中",
    "fa": "發",
    "bai": "白",
}
BONUS_LABELS = {
    35: "春",
    36: "夏",
    37: "秋",
    38: "冬",
    39: "梅",
    40: "蘭",
    41: "菊",
    42: "竹",
}

# The association page maps flowers by number/name:
# 東: 1/梅/春, 南: 2/蘭/夏, 西: 3/竹/秋, 北: 4/菊/冬.
SEAT_BONUS_TILES = {
    "east": {35, 39},
    "south": {36, 40},
    "west": {37, 42},
    "north": {38, 41},
}

SPECIAL_EVENT_DEFAULT_TAI = {
    "heavenly_win": 24,
    "human_win": 16,
    "earthly_win": 16,
    "heavenly_ready": 16,
    "earthly_ready": 8,
    "seven_robbing_one": 8,
    "rob_kong": 1,
    "kong_draw": 1,
    "last_discard": 1,
    "last_tile": 1,
}

TRUE_VALUES = {"1", "true", "yes", "y", "on", "self", "tsumo"}
SELF_DRAW_ALIASES = {"self", "self_draw", "self-draw", "tsumo", "zimo", "自摸"}
WIND_ALIASES = {
    "e": "east",
    "east": "east",
    "東": "east",
    "dong": "east",
    "s": "south",
    "south": "south",
    "南": "south",
    "nan": "south",
    "w": "west",
    "west": "west",
    "西": "west",
    "xi": "west",
    "n": "north",
    "north": "north",
    "北": "north",
    "bei": "north",
}
