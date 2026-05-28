from chixiao.core.config import Settings, load_config


class TestConfig:
    def test_default_settings(self):
        settings = Settings()
        assert settings.data_source == "akshare"
        assert settings.execution_mode == "mode_a"
        assert settings.risk_max_position_pct == 0.25

    def test_load_config_from_yaml(self, tmp_path):
        yaml_content = """
data_source: akshare
execution_mode: mode_a
risk_max_position_pct: 0.3
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)
        settings = load_config(config_file)
        assert settings.risk_max_position_pct == 0.3

    def test_load_config_missing_file_uses_defaults(self):
        settings = load_config("/nonexistent/config.yaml")
        assert settings.data_source == "akshare"
