import os

from openai import OpenAI

def get_inference_client() -> OpenAI:

    cleint = OpenAI(
        key=os.environ.get("OPENAI_API_KEY")
    )

    return cleint