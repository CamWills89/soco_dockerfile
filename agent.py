import json
import time
import re
import logging
from typing import List, Tuple
from llm_backend import Backend  
from prompts import JSON_prompt, validation_prompt, corrector_prompt  
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods

class Agent:
    def __init__(
        self,
        json_backend: Backend,
        validation_backend: Backend,
        correction_backend: Backend,
        max_iterations: int = 5,
    ):
        """
        Initializes the Agent with separate Backends for JSON generation, validation, and correction.

        Args:
            json_backend (Backend): Backend instance for JSON generation.
            validation_backend (Backend): Backend instance for JSON validation.
            correction_backend (Backend): Backend instance for JSON correction.
            max_iterations (int): Maximum number of attempts to validate/correct JSON.
        """
        self.json_backend = json_backend
        self.validation_backend = validation_backend
        self.correction_backend = correction_backend
        self.max_iterations = max_iterations

    def generate_json(self, user_input: str) -> str:
        """
        Generates JSONs based on user input using the JSON_prompt, concatenates them into a single string.

        Args:
            user_input (str): The input from the user.

        Returns:
            str: The concatenated JSON strings.

        Raises:
            ValueError: If JSON extraction fails.
        """
        prompt = JSON_prompt.format(input=user_input)
        response = self.json_backend.generate_response(prompt=prompt)
        # Extract all JSON instances between <JSON> and </JSON> tags
        json_matches = re.findall(r"<JSON>\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*</JSON>", response, re.IGNORECASE)
        if json_matches:
            # Concatenate all JSON strings into a single string
            concatenated_json = '\n'.join(json_matches)
            return concatenated_json
        else:
            print("Failed to extract JSON from the JSON generation response.")
            print(f"Full JSON Generation Response:\n{response}\n")
            raise ValueError("Failed to extract JSON from the response.")

    def validate_json(self, user_input: str, generated_json: str) -> Tuple[bool, str, str, str]:
        """
        Validates the concatenated JSON string based on user input using the validation_prompt.

        Args:
            user_input (str): The input from the user.
            generated_json (str): The concatenated JSON string to validate.

        Returns:
            tuple:
                bool: Indicates if the JSON is correct.
                str: Issues identified (if any).
                str: Recommendations for correction (if any).
                str: Validation status ("Correct" or "Incorrect").
        """
        prompt = validation_prompt.format(input=user_input, JSON=generated_json)
        response = self.validation_backend.generate_response(prompt=prompt)
        response = response.strip()

        print("\n--- Full Validation Response ---")
        print(response)
        print("--- End of Validation Response ---\n")

        status_match = re.search(r"<status>\s*(Correct|Incorrect)\s*</status>", response, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).strip()
            is_correct = status.lower() == "correct"
        else:
            is_correct = False
            status = "Incorrect"


        issues_match = re.search(r"<issues>\s*([\s\S]*?)\s*</issues>", response, re.IGNORECASE)
        issues = issues_match.group(1).strip() if issues_match else ""

        recommendations_match = re.search(r"<recommendation>\s*([\s\S]*?)\s*</recommendation>", response, re.IGNORECASE)
        recommendations = recommendations_match.group(1).strip() if recommendations_match else ""

        return is_correct, issues, recommendations, status

    def correct_json(self, issues: str, recommendations: str, generated_json: str) -> str:
        """
        Corrects the concatenated JSON string based on issues and recommendations using the corrector_prompt.

        Args:
            issues (str): The issues identified in the JSON.
            recommendations (str): Recommendations for correcting the JSON.
            generated_json (str): The concatenated JSON string to correct.

        Returns:
            str: The corrected concatenated JSON string.
        """
        prompt = corrector_prompt.format(issues=issues, recommendations=recommendations, JSON=generated_json)
        response = self.correction_backend.generate_response(prompt=prompt)
        response = response.strip()

        print("\n--- Full Correction Response ---")
        print(response)
        print("--- End of Correction Response ---\n")

        corrected_json_match = re.search(r"<JSON>\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*</JSON>", response, re.IGNORECASE | re.MULTILINE)
        if corrected_json_match:
            corrected_json = corrected_json_match.group(1).strip()
            return corrected_json
        else:
            print("Warning: Corrected JSON not found in the correction response.")
            print(f"Correction Response:\n{response}\n")
            raise ValueError("Failed to extract corrected JSON from the response.")

    def is_valid_json(self, json_str: str) -> bool:
        """
        Checks if a string is valid JSON.

        Args:
            json_str (str): The JSON string to check.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError:
            return False

    def run(self, user_input: str) -> List[dict]:
        """
        Runs the agent to generate, validate, and correct JSON based on user input.

        Args:
            user_input (str): The input from the user.

        Returns:
            List[dict]: The final validated JSON objects.

        Raises:
            Exception: If the JSON could not be validated after maximum iterations.
        """
        try:
            generated_json = self.generate_json(user_input)
        except ValueError as ve:
            print(f"Error during JSON generation: {ve}\n")
            raise

        iteration = 0
        while iteration < self.max_iterations:
            print(f"\nIteration {iteration + 1}:")
            print("Generated JSON:")
            print(generated_json)
            print("\nValidating JSON...")

            try:
                is_correct, issues, recommendations, status = self.validate_json(user_input, generated_json)
            except Exception as e:
                print(f"Error during validation: {e}\n")
                raise

            print("Validation Response:")
            print(f"Status: {status}")
            print("Issues Identified:")
            print(issues)
            print("Recommendations:")
            print(recommendations)

            if is_correct and self.is_valid_json(generated_json):
                print("JSON is valid and correct.\n")
                validated_json = json.loads(generated_json)
                if isinstance(validated_json, list):
                    for idx, json_obj in enumerate(validated_json):
                        filename = f"validated_output_{idx + 1}.json"
                        self.store_json(json.dumps(json_obj), filename)
                else:
                    self.store_json(json.dumps(validated_json), "validated_output.json")
                return validated_json
            else:
                try:
                    generated_json = self.correct_json(issues, recommendations, generated_json)
                except Exception as e:
                    print(f"Error during correction: {e}\n")
                    break  
            iteration += 1

        print("Failed to generate valid JSON after maximum iterations.\n")
        raise Exception("Failed to generate valid JSON after maximum iterations.")

    def store_json(self, json_str: str, filename: str):
        """
        Stores the validated JSON string into a JSON file.

        Args:
            json_str (str): The JSON string to store.
            filename (str): The name of the file to store the JSON.
        """
        try:
            json_data = json.loads(json_str)
            with open(filename, 'w') as f:
                json.dump(json_data, f, indent=4)
            print(f"Validated JSON stored in '{filename}'.\n")
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON for storage: {e}\n")
        except Exception as e:
            print(f"Failed to store JSON: {e}\n")

def main():
    json_backend = Backend(
        model_id="meta-llama/llama-3-70b-instruct",
        model_params={
            "decoding_method": DecodingMethods.GREEDY,
            "min_new_tokens": 1,
            "max_new_tokens": 1500,
            "repetition_penalty": 1,
            "random_seed": 42,
        }
    )

    validation_backend = Backend(
        model_id="mistralai/mixtral-8x7b-instruct-v01",
        model_params={
            "decoding_method": DecodingMethods.GREEDY,
            "min_new_tokens": 1,
            "max_new_tokens": 2000,
            "repetition_penalty": 1,
            "random_seed": 42,
        }
    )

    correction_backend = Backend(
        model_id="meta-llama/llama-3-70b-instruct",
        model_params={
            "decoding_method": DecodingMethods.GREEDY,
            "min_new_tokens": 1,
            "max_new_tokens": 1500,
            "repetition_penalty": 1,
            "random_seed": 42,
        }
    )

    agent = Agent(
        json_backend=json_backend,
        validation_backend=validation_backend,
        correction_backend=correction_backend,
        max_iterations=5
    )

    user_input = "On September 26, 2024, at 1:00 PM, elevated user secure_user attempted to log into secure_access_db but failed both password entry and two-factor authentication, resulting in 10 consecutive failed attempts within 10 minutes."
    try:
        final_jsons = agent.run(user_input)
        print("\nFinal Validated JSONs:")
        if isinstance(final_jsons, list):
            for idx, json_obj in enumerate(final_jsons):
                print(f"\nJSON #{idx + 1}:")
                print(json.dumps(json_obj, indent=4))
        else:
            print(json.dumps(final_jsons, indent=4))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
