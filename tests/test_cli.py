from datetime import datetime, timezone
from bragdoc.cli import main
from bragdoc.models import WorkItem
from bragdoc.aggregator import write_cache


def _item():
    return WorkItem("github_pr", "aproxy-operator", "canonical", "PS7",
                    "https://x/1", datetime(2026, 5, 1, tzinfo=timezone.utc),
                    "author", "merged", "#1", {})


def _config_files(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "identity:\n"
        "  github_username: octo\n"
        "date_range:\n"
        "  start: \"2026-03-01\"\n"
        "  end: \"2026-09-01\"\n"
        "scope:\n"
        "  github_orgs: []\n"
        "  main_projects: [aproxy-operator]\n"
        "sources: {}\n"
    )
    env = tmp_path / ".env"
    env.write_text("")
    return cfg, env


def test_render_command_reads_cache_and_writes_output(tmp_path):
    cfg, env = _config_files(tmp_path)
    cache = tmp_path / "cache.json"
    write_cache([_item()], str(cache))
    out = tmp_path / "digest.md"
    rc = main([
        "render",
        "--config", str(cfg),
        "--env", str(env),
        "--cache", str(cache),
        "--output", str(out),
    ])
    assert rc == 0
    text = out.read_text()
    assert "# Brag Digest — octo" in text
    assert "aproxy-operator" in text


def test_render_command_also_writes_companion_prompt_file(tmp_path):
    cfg, env = _config_files(tmp_path)
    cache = tmp_path / "cache.json"
    write_cache([_item()], str(cache))
    out = tmp_path / "digest.md"
    rc = main([
        "render",
        "--config", str(cfg),
        "--env", str(env),
        "--cache", str(cache),
        "--output", str(out),
    ])
    assert rc == 0
    prompt_path = tmp_path / "digest-prompt.md"
    assert prompt_path.exists()
    text = prompt_path.read_text()
    assert "digest.md" in text
    assert "1-2 page" in text


def test_prompt_command_writes_prompt_without_needing_cache(tmp_path):
    cfg, env = _config_files(tmp_path)
    out = tmp_path / "digest.md"
    rc = main([
        "prompt",
        "--config", str(cfg),
        "--env", str(env),
        "--output", str(out),
    ])
    assert rc == 0
    prompt_path = tmp_path / "digest-prompt.md"
    assert prompt_path.exists()
