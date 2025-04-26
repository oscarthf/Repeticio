
from openai import OpenAI

def get_inference_client() -> OpenAI:

    cleint = OpenAI()

    return cleint