import json
import logging
logger = logging.getLogger('persistence_config', level=logging.INFO)

class ComunicationWindowConfig:
    """config window size via W_size(Max Limit) = Token(Model_max) − Token(System_prompt) − Token(Model_output) − Token(Tool/Rag_context) from config.json"""
    def __init__(self, model_name: str):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                model_config = config["model_name"]
                model_context_size_limit = int(model_config["model_context_size_limit"]) * 0.8 or 102400
                token_system_prompt_size_limit = model_config["token_system_prompt_size_limit"] or 128000
                token_output_size_limit = model_config["token_output_size_limit"] or 128000
                token_tools_size_limit = model_config["token_tools_size_limit"] or 128000
                if token_system_prompt_size_limit + token_output_size_limit + token_tools_size_limit > model_context_size_limit:
                    logger.warning(f"Error: config.json token_system_prompt_size_limit, token_output_size_limit, and token_tools_size_limit must be less than or equal to model_context_size_limit * 0.8: {model_context_size_limit}")
                    raise ValueError("token_system_prompt_size_limit, token_output_size_limit, and token_tools_size_limit must be less than or equal to model_context_size_limit")
        except Exception as e:
            logger.warning(f"Error loading config.json: {e}, using default values: window_model_context_size=128000, step_size=128")
            window_model_context_size = 128000
            step_size = 128
