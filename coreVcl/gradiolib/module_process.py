import os
import torch
from typing import Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM

class translate_module:
    def __init__(self, path:str = "../saved_model")->None:
        self.model_dir:str = path
        self.model:Any = None
        self.tokenizer:Any = None
        self.device:str = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self)->bool:
        if not os.path.exists(self.model_dir):
            print(f"can not find {self.model_dir}, stop load")
            return False

        print(f"Loading model from {self.model_dir}")
    
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, padding_side='left')
        self.model = AutoModelForCausalLM.from_pretrained(self.model_dir).to(self.device)

        if self.tokenizer is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.padding_side = "left"


        self.model.generation_config.padding_side = 'left'
        self.model.generation_config.pad_token_id = self.tokenizer.eos_token_id

        return True
    
    def translate(self, text:str) -> str:
        prompt_template = "Translate Chinese to English: {} =>"
        prompt = prompt_template.format(text)

        inputs = self.tokenizer(prompt, return_tensors='pt').to(self.device)

        with torch.no_grad():
            outputs= self.model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=5,
                early_stopping=True,
                pad_token_id= self.tokenizer.eos_token_id
            )

        decoded_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return decoded_output.replace(prompt, "").strip()


        # input_len = inputs["input_ids"].shape[1]
        # new_tokens = outputs[0][input_len:]
        # decoded_output = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        # ss = decoded_output.replace(prompt, "").strip()
        # print(f"Result: {ss}")
        # return ss
        # print(f"{decoded_output.replace(prompt, '').strip()}")
        # return decoded_output.replace(prompt, "").strip()
        # print(f"{self.tokenizer.decode(outputs[0], skip_special_tokens=True)}")
        # return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    


