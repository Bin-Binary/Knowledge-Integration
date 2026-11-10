
import json
from typing import List, Dict, Union
import tiktoken
import logging
logger = logging.getLogger(__name__)
SAFE_FACTOR = 0.9
TOKEN_MODEL_OUTPUT = 4096
DEFAULT_TOKEN_MODEL_MAX = 128000

class WindowConfig():
    """Config static chat window static boundary via formula: 
    @window size: 
    • Static Boundary Formula: $$W_\text{input\_safe} = (\text{Token}_\text{Mode\_max} \times \text{Safe\_Factor}) - \text{Token}_\text{System\_Prompt} - \text{Token}_\text{Mode\_output}$$
    """
    def __init__(
        self, 
        model: str,
        prompts: Union[str, List[str], Dict[str, str]]
    ) -> None:
        model_spec = {}
        try:
            with open('./persistence_config.json', 'r', encoding='UTF-8') as f:
                config_info = json.load(f)
                if model in config_info:
                    model_spec = config_info[model]
                else:
                    logger.warning(f'Model: {model} not found in config. Using global defaults')
        except Exception as e:
            logger.warning(
                f'Load persistence_config.json failed, cause: {e}.'
                f'Falling back to defaults -> max: {DEFAULT_TOKEN_MODEL_MAX}, safe_factor:{SAFE_FACTOR}, output: {TOKEN_MODEL_OUTPUT}'
            )
        self.encoder = tiktoken.get_encoding(model_spec.get('encoding_name', 'cl100k_base'))
        self.token_model_max = model_spec.get('token_model_max', DEFAULT_TOKEN_MODEL_MAX)
        self.safe_factor = model_spec.get('safe_factor', SAFE_FACTOR)
        self.token_model_output = model_spec.get('token_model_output', TOKEN_MODEL_OUTPUT)
        self.full_prompts_text = self._aggregate_prompts(prompts)
        self.token_system_prompt = len(self.encoder.encode(self.full_prompts_text))
        self.w_input_safe = int(self.token_model_max * self.safe_factor) - self.token_system_prompt - self.token_model_output

        if self.w_input_safe <= 0:
            logger.critical(
                f"[Prompt Overflow Alarm] The current aggregated prompt size ({self.token_system_prompt} Tokens) has severely expanded!"
                f"It has exceeded the safe pool limit of the current model [{model}], leaving a negative space for conversation history and RAG ({self.w_input_safe})!"
                f"Please immediately perform dynamic tool description pruning (Tool Pruning) or reduce the number of Few-Shot examples!"
            )

    def _aggregate_prompts(self, prompts: Union[str, List[str], Dict[str, str]]) -> str:
        """Combine scattered prompts to structure text, e.g, Markdown XML
        1. When handling input from Dict, enforce a forward sorting (Sorted Keys) to ensure hash consistency and maximize the benefits of the Prompt Cache.
        2. Monitor list and dictionary segments.
        """
        if isinstance(prompts, str):
            self.prompt_fragments_count = 1
            return prompts
                
        if isinstance(prompts, list):
            self.prompt_fragments_count = len(prompts)
            return "\n\n".join(prompts)
                
        if isinstance(prompts, dict):
            self.prompt_fragments_count = len(prompts)
            aggregated_list = []
            ordered_keys = sorted(prompts.keys())
            
            for tag in ordered_keys:
                text = prompts[tag]
                aggregated_list.append(f"<{tag}>\n{text}\n</{tag}>")
            return "\n".join(aggregated_list)
        return ""
