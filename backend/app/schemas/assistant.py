from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_ASSISTANT_NAME = "Business Assistant"
DEFAULT_WELCOME_MESSAGE = "Hi! Ask me anything about our business."
DEFAULT_FALLBACK_MESSAGE = (
    "Sorry, I couldn't find relevant information "
    "in the available documents."
)


class AssistantSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default=DEFAULT_ASSISTANT_NAME, min_length=1, max_length=60)
    welcome_message: str = Field(
        default=DEFAULT_WELCOME_MESSAGE, min_length=1, max_length=300
    )
    fallback_message: str = Field(
        default=DEFAULT_FALLBACK_MESSAGE, min_length=1, max_length=300
    )

    @field_validator("name", "welcome_message", "fallback_message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or whitespace.")
        return value