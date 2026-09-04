from __future__ import annotations

import argparse
import os
from datetime import datetime

from bragdoc.aggregator import collect, read_cache, write_cache
from bragdoc.config import load_config
from bragdoc.fetchers.registry import all_fetchers
from bragdoc.prompt import render_prompt
from bragdoc.renderer import render_markdown


def _default_output() -> str:
    return f"output/brag-digest-{datetime.now().date().isoformat()}.md"


def _prompt_path(output_path: str) -> str:
    root, ext = os.path.splitext(output_path)
    return f"{root}-prompt{ext or '.md'}"


def _do_fetch(config, cache_path: str) -> None:
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    items = collect(config, all_fetchers())
    write_cache(items, cache_path)
    print(f"[bragdoc] wrote {len(items)} items to {cache_path}")


def _do_render(config, cache_path: str, output_path: str) -> None:
    items = read_cache(cache_path)
    md = render_markdown(
        items,
        main_projects=config.main_projects,
        username=config.identity.get("github_username", "me"),
        window=(config.window_start, config.window_end),
    )
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"[bragdoc] wrote digest to {output_path}")
    _do_prompt(config, output_path)


def _do_prompt(config, output_path: str) -> None:
    prompt_path = _prompt_path(output_path)
    text = render_prompt(
        username=config.identity.get("github_username", "me"),
        goals_this_year=config.goals.get("this_year", ""),
        goals_next_year=config.goals.get("next_year", ""),
        digest_filename=os.path.basename(output_path),
    )
    os.makedirs(os.path.dirname(prompt_path) or ".", exist_ok=True)
    with open(prompt_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"[bragdoc] wrote LLM prompt to {prompt_path}")


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="config.yaml")
    common.add_argument("--env", default=".env")
    common.add_argument("--cache", default="cache/workitems.json")
    common.add_argument("--output", default=None)

    parser = argparse.ArgumentParser(prog="bragdoc", parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch", parents=[common])
    sub.add_parser("render", parents=[common])
    sub.add_parser("run", parents=[common])
    sub.add_parser("prompt", parents=[common])
    args = parser.parse_args(argv)

    config = load_config(args.config, args.env)
    output = args.output or _default_output()

    if args.command == "fetch":
        _do_fetch(config, args.cache)
    elif args.command == "render":
        _do_render(config, args.cache, output)
    elif args.command == "run":
        _do_fetch(config, args.cache)
        _do_render(config, args.cache, output)
    elif args.command == "prompt":
        _do_prompt(config, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
