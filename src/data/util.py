from dotenv import load_dotenv
from joblib.memory import Memory

load_dotenv()
memory = Memory(location=".cache", verbose=0)
cache = memory.cache
