import pytest

from app.core.config import Settings


def test_budgets_defaults_match_spec():
    s = Settings()
    assert (s.max_model_calls, s.max_mcp_calls, s.max_pipeline_seconds) == (6, 3, 60)


def test_default_secrets_rejected_outside_dev():
    with pytest.raises(RuntimeError):
        Settings(app_env="prod").assert_safe_for_prod()
    Settings(app_env="dev-cpu").assert_safe_for_prod()


def test_device_auto_falls_back_to_cpu_without_torch():
    from app.core.config import resolve_device

    assert resolve_device("cpu") == "cpu"
    assert resolve_device("auto") in ("cpu", "cuda")
