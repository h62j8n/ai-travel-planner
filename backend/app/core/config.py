from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    # OpenRouter (백엔드 전용 — 클라이언트에 노출 금지, PRD §8.2 / §11)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # 무료 모델은 업스트림 rate-limit(429)이 수시로 걸리므로 단일 모델 대신
    # 폴백 체인을 쓴다. 하나가 429/실패면 다음 모델로 넘어간다 (§7, §10.1).
    # OPENROUTER_MODEL(단일)을 지정하면 그 모델이 체인 맨 앞에 온다.
    openrouter_model: str = ""
    openrouter_models: str = (
        "openai/gpt-oss-120b:free,"
        "nvidia/nemotron-3-super-120b-a12b:free,"
        "openai/gpt-oss-20b:free,"
        "meta-llama/llama-3.3-70b-instruct:free,"
        "openrouter/free"
    )

    # AI 호출 타임아웃 (§10.1): 모델당 20초
    ai_timeout_seconds: float = 20.0

    @property
    def model_list(self) -> list[str]:
        prefer = [self.openrouter_model.strip()] if self.openrouter_model.strip() else []
        rest = [m.strip() for m in self.openrouter_models.split(",") if m.strip()]
        seen: set[str] = set()
        out: list[str] = []
        for m in (*prefer, *rest):
            if m not in seen:
                seen.add(m)
                out.append(m)
        return out


settings = Settings()
