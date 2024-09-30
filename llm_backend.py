
import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

load_dotenv()

class Backend:
    def __init__(
        self,
        model_id: str,
        model_params: dict,
    ):
        """
        Initializes the Model instance for a given model ID and generation parameters.

        Args:
            model_id (str): The identifier for the LLM model to use.
            model_params (dict): The generation parameters specific to the model.
        """
        api_key = os.getenv("IBM_CLOUD_API_KEY", None)
        ibm_cloud_url = os.getenv("IBM_CLOUD_ENDPOINT", None)
        project_id = os.getenv("IBM_CLOUD_PROJECT_ID", None)

        if api_key is None or ibm_cloud_url is None or project_id is None:
            raise Exception(
                "Ensure you have a .env file with IBM_CLOUD_API_KEY, IBM_CLOUD_ENDPOINT, and IBM_CLOUD_PROJECT_ID."
            )

        self.model_id = model_id
        self.model_params = model_params

        self.model = Model(
            model_id=self.model_id,
            params=self.model_params,
            credentials=Credentials(url=ibm_cloud_url, api_key=api_key),
            project_id=project_id,
        )

    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using the LLM based on the provided prompt.

        Args:
            prompt (str): The prompt for generating the response.
            **kwargs: Additional keyword arguments for customization.

        Returns:
            str: The generated response.
        """
        result = self.model.generate_text(prompt, **kwargs)
        return result

    def generate_stream_response(self, prompt: str, **kwargs):
        """
        Generate a streaming response using the LLM based on the provided prompt.

        Args:
            prompt (str): The prompt for generating the response.
            **kwargs: Additional keyword arguments for customization.

        Returns:
            generator: A generator yielding chunks of the response.
        """
        generator = self.model.generate_text_stream(prompt, **kwargs)
        return generator
