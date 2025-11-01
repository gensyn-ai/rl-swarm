import hashlib
from functools import lru_cache
from typing import Sequence

# fmt: off
ADJECTIVES = [
    "agile", "alert", "amphibious", "aquatic", "arctic", "armored", "barky", "beaked",
    "bellowing", "bipedal", "bold", "bristly", "burrowing", "camouflaged", "carnivorous", "chattering",
    "clawed", "climbing", "coiled", "colorful", "crested", "cunning", "curious", "dappled",
    "darting", "deadly", "deft", "dense", "dextrous", "diving", "docile", "domestic",
    "dormant", "downy", "durable", "eager", "elusive", "endangered", "energetic", "enormous",
    "exotic", "extinct", "fanged", "fast", "feathered", "feline", "ferocious", "fierce",
    "finicky", "fishy", "flapping", "fleecy", "flexible", "flightless", "fluffy", "foraging",
    "foxy", "freckled", "frisky", "furry", "galloping", "gentle", "giant", "gilded",
    "gliding", "graceful", "grassy", "grazing", "gregarious", "grunting", "hairy", "hardy",
    "hibernating", "hoarse", "horned", "howling", "huge", "hulking", "humming", "hunting",
    "insectivorous", "invisible", "iridescent", "jagged", "jumping", "keen", "knobby", "lanky",
    "large", "lazy", "leaping", "leggy", "lethal", "lightfooted", "lithe", "lively",
    "long", "loud", "lumbering", "majestic", "mammalian", "mangy", "marine", "masked",
    "meek", "melodic", "mighty", "mimic", "miniature", "moist", "monstrous", "mottled",
    "muscular", "mute", "nasty", "nimble", "nocturnal", "noisy", "omnivorous", "opaque",
    "padded", "pale", "patterned", "pawing", "peaceful", "peckish", "pensive", "pesty",
    "placid", "playful", "plump", "poisonous", "polished", "pouncing", "powerful", "prehistoric",
    "prickly", "prowling", "pudgy", "purring", "quick", "quiet", "rabid", "raging",
    "rangy", "rapid", "ravenous", "reclusive", "regal", "reptilian", "restless", "roaring",
    "robust", "rough", "rugged", "running", "savage", "scaly", "scampering", "scavenging",
    "scented", "screeching", "scruffy", "scurrying", "secretive", "sedate", "shaggy", "sharp",
    "shiny", "short", "shrewd", "shy", "silent", "silky", "singing", "sizable",
    "skilled", "skittish", "sleek", "slender", "slimy", "slithering", "slow", "sly",
    "small", "smooth", "snappy", "sneaky", "sniffing", "snorting", "soaring", "soft",
    "solitary", "spotted", "sprightly", "squeaky", "squinting", "stalking", "stealthy", "stinging",
    "stinky", "stocky", "striped", "strong", "stubby", "sturdy", "subtle", "swift",
    "tall", "tame", "tangled", "tawny", "tenacious", "territorial", "thick", "thorny",
    "thriving", "timid", "tiny", "toothy", "tough", "tricky", "tropical", "trotting",
    "twitchy", "unseen", "untamed", "vicious", "vigilant", "vocal", "voracious", "waddling",
    "wary", "webbed", "whiskered", "whistling", "wild", "wily", "winged", "wiry",
    "wise", "woolly", "yapping", "yawning", "zealous"
]

ANIMALS = [
    "aardvark", "albatross", "alligator", "alpaca", "anaconda", "ant", "anteater", "antelope",
    "ape", "armadillo", "baboon", "badger", "barracuda", "bat", "bear", "beaver",
    "bee", "bison", "boar", "bobcat", "buffalo", "butterfly", "camel", "capybara",
    "caribou", "cassowary", "cat", "caterpillar", "cheetah", "chicken", "chameleon", "chimpanzee",
    "chinchilla", "clam", "cobra", "cockroach", "cod", "condor", "coral", "cougar", "cow",
    "coyote", "crab", "crane", "crocodile", "crow", "deer", "dingo", "dinosaur",
    "dog", "dolphin", "donkey", "dove", "dragonfly", "duck", "eagle", "eel",
    "elephant", "elk", "emu", "falcon", "ferret", "finch", "fish", "flamingo",
    "flea", "fly", "fox", "frog", "gazelle", "gecko", "gerbil", "gibbon",
    "giraffe", "goat", "goose", "gorilla", "grasshopper", "grouse", "gull", "hamster",
    "hare", "hawk", "hedgehog", "heron", "hippo", "hornet", "horse", "hummingbird",
    "hyena", "ibis", "iguana", "impala", "jackal", "jaguar", "jay", "jellyfish",
    "kangaroo", "kingfisher", "kiwi", "koala", "komodo", "ladybug", "lemur", "leopard",
    "lion", "lizard", "llama", "lobster", "locust", "lynx", "macaque", "macaw",
    "magpie", "mallard", "mammoth", "manatee", "mandrill", "mantis", "marmot", "meerkat",
    "mink", "mole", "mongoose", "monkey", "moose", "mosquito", "mouse", "mule",
    "narwhal", "newt", "nightingale", "ocelot", "octopus", "okapi", "opossum", "orangutan", "ostrich",
    "otter", "owl", "ox", "panda", "panther", "parrot", "peacock", "pelican",
    "penguin", "pheasant", "pig", "pigeon", "piranha", "platypus", "porcupine", "porpoise",
    "prawn", "puffin", "puma", "python", "quail", "rabbit", "raccoon",
    "ram", "rat", "raven", "reindeer", "rhino", "robin", "rooster", "salamander",
    "salmon", "sandpiper", "sardine", "scorpion", "seahorse", "seal", "sealion",
    "shark", "sheep", "shrew", "shrimp", "skunk", "sloth", "slug", "snail",
    "snake", "sparrow", "spider", "squid", "squirrel", "starfish", "stingray", "stork",
    "swan", "tamarin", "tapir", "tarantula", "termite", "tiger", "toad", "tortoise",
    "toucan", "trout", "tuna", "turkey", "turtle", "viper", "vulture", "wallaby",
    "walrus", "warthog", "wasp", "weasel", "whale", "wildebeest", "wolf", "wombat",
    "woodpecker", "worm", "yak", "zebra"
]
# fmt: on


def hex_to_ints(s, k):
    """Converts hex-encoded strings to int lists. Specify chunk size with k."""
    return tuple(int(s[i : i + k], 16) for i in range(0, len(s), k))


# libp2p peer IDs are always base58-encoded multihashes!


@lru_cache
def get_name_from_peer_id(peer_id: str, no_spaces=False):
    # ~200 entries for both lists; so 2 hex digits.
    ints = hex_to_ints(hashlib.md5(peer_id.encode()).hexdigest(), 2)
    adj1 = ADJECTIVES[ints[2] % len(ADJECTIVES)]
    adj2 = ADJECTIVES[ints[1] % len(ADJECTIVES)]
    animal = ANIMALS[ints[0] % len(ANIMALS)]

    name = f"{adj1} {adj2} {animal}"
    if no_spaces:
        name = "_".join(name.split(" "))
    return name


def search_peer_ids_for_name(peer_ids: Sequence[str], name):
    for peer_id in peer_ids:
        if name == get_name_from_peer_id(peer_id):
            return peer_id
    return None
