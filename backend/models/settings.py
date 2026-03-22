from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SettingItem(BaseModel):
    key: str
    value: str
    is_secret: bool = False


class SettingsUpdate(BaseModel):
    settings: list[SettingItem]


class SettingsOut(BaseModel):
    category: str
    settings: list[dict]


class TestLLMRequest(BaseModel):
    provider: str = "openai"
    api_base: str
    api_key: str
    model: str


class TestTushareRequest(BaseModel):
    token: str


class AgentConfigOut(BaseModel):
    id: int
    cluster: str
    agent_name: str
    display_name: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    is_enabled: bool = True
    parameters: Optional[str] = None


class AgentConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    is_enabled: Optional[bool] = None
    parameters: Optional[str] = None


class NewsSourceCreate(BaseModel):
    name: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True
    fetch_interval: int = 3600
    category: str = ""
    market: str = ""
    dedup_strategy: str = "content_hash"
    parser: str = ""
    priority: float = 0.5
    credibility: float = 0.5


class NewsSourceOut(BaseModel):
    id: int
    name: str
    type: str
    config: Dict[str, Any]
    is_enabled: bool
    fetch_interval: int
    category: str = ""
    market: str = ""
    dedup_strategy: str = "content_hash"
    parser: str = ""
    priority: float = 0.5
    credibility: float = 0.5
    last_fetched: Optional[str] = None
