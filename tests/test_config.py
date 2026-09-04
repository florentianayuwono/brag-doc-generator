from datetime import datetime
from bragdoc.config import Config, load_config

CONFIG_YAML = """
identity:
  github_username: octocat
  jira_email: me@example.com
  jira_server: https://example.atlassian.net
  discourse_base_url: https://discourse.example.com
  discourse_username: octo
  launchpad_user: octo
date_range:
  months_back: 6
scope:
  github_orgs: [acme]
  main_projects: [widget]
sources:
  github_prs: true
  jira: false
"""


def _write(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CONFIG_YAML)
    env = tmp_path / ".env"
    env.write_text("GITHUB_TOKEN=abc\n")
    return cfg, env


def test_load_config_parses_identity_and_scope(tmp_path):
    cfg, env = _write(tmp_path)
    c = load_config(str(cfg), str(env))
    assert c.identity["github_username"] == "octocat"
    assert c.github_orgs == ["acme"]
    assert c.main_projects == ["widget"]


def test_window_from_months_back(tmp_path):
    cfg, env = _write(tmp_path)
    c = load_config(str(cfg), str(env))
    span_days = (c.window_end - c.window_start).days
    assert 170 <= span_days <= 190  # ~6 months


def test_explicit_dates_override(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CONFIG_YAML.replace(
        "  months_back: 6",
        '  months_back: 6\n  start: "2026-01-01"\n  end: "2026-02-01"',
    ))
    env = tmp_path / ".env"
    env.write_text("")
    c = load_config(str(cfg), str(env))
    assert c.window_start == datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    assert c.window_end == datetime.fromisoformat("2026-02-01T00:00:00+00:00")


def test_source_enabled_requires_toggle(tmp_path):
    cfg, env = _write(tmp_path)
    c = load_config(str(cfg), str(env))
    assert c.source_enabled("github_prs") is True
    assert c.source_enabled("jira") is False
    assert c.source_enabled("discourse") is False  # absent -> default False
