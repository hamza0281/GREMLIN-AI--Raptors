import os

class CLIConfig:
    # Default settings for the CLI execution
    DEFAULT_DURATION = 60
    DEFAULT_OUTPUT_DIR = "reports"
    
    # Model specification as per hackathon requirement
    MODEL_NAME = "Qwen 3 0.6B Q4_K_M"
    MODEL_PROVIDER = "Ollama"
    
    # Target fallback
    API_URL = os.getenv("CHAOS_API_URL", "http://localhost:8000")
    
    # Personas configuration
    AVAILABLE_PERSONAS = [
        "grandma",
        "hacker",
        "speed_demon",
        "toddler",
        "overthinking_dev",
        "international_traveler"
    ]
