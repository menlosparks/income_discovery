
from google import genai
import time


SYSTEM_INSTRUCTION = """
You are a helpful financial advisor. Give concise answers to the user's questions. Limit
the answers to 3 or 4 sentences. If the answer is not in the documents, say so. 
You have access to the user_data in JSON format to retrieve information about the user's 
spouse, income, and account balances. In every response include a reference to the relevant
field in the  user data which is provided in the JSON object.
Always make calculations based on the user data, be sure of the calculations and provide the answer in a clear and concise manner. 
Do not exceed 100 words in your response. 
"""

MODEL_NAME = 'gemini-2.5-flash'


def call_shared_llm(prompt: str, client):
    while True:
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt);
            usage = response.usage_metadata
            print(f"Prompt tokens: {usage.prompt_token_count} Candidates tokens: {usage.candidates_token_count} Total tokens: {usage.total_token_count}")
            return response, usage

        except genai.errors.ServerError as e:
            print(f"Server busy error: {e}")
            print("Retrying in 10 seconds... Hit Ctrl-C to exit")
            time.sleep(10)
            continue
        except genai.errors.ClientError as e:
            print(f"Client error: {e}")
            if (e.code == 429):
                print("Retrying in 20 seconds... Hit Ctrl-C to exit")
                time.sleep(20)
                continue
            else:
                print("Severe error exiting")
                raise e
        except Exception as e:
            print(f"Error: {e}")
            raise e