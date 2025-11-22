class Settings:
    """
    Global configuration for the autonomous browser agent platform.
    Supports multiple LLM providers (LangChain, Amazon Bedrock, etc.).
    """

    # Browser settings
    BROWSER_TIMEOUT = 30  # seconds
    BROWSER_HEADLESS = True
    BROWSER_VIEWPORT = {"width": 1920, "height": 1080}

    # Agent / LLM settings
    # Supported providers: "langchain", "amazon_bedrock"
    LLM_PROVIDER = "langchain"  # or "amazon_bedrock"

    # LangChain / generic LLM settings
    LLM_MODEL = "gpt-4o-mini"
    LLM_BASE_URL = "https://api.openai.com/v1"
    LLM_API_TOKEN = "your_langchain_api_token_here"
    LLM_MAX_TOKENS = 2000

    # Amazon Bedrock settings (if LLM_PROVIDER == "amazon_bedrock")
    AWS_REGION = "us-east-1"
    AWS_BEARER_TOKEN = "your_aws_bearer_token_here"
    AWS_MODEL_ID = "amazon_model_id_here"
    AWS_TIMEOUT = 30  # seconds for Bedrock API calls

    # Task / Queue settings
    MAX_RETRIES = 3
    TASK_CONCURRENCY = 2

    # Logging
    LOG_FILE = "system.log"
