from bragdoc.prompt import render_prompt


def test_prompt_includes_template_sections_in_order():
    text = render_prompt(username="octo", goals_this_year="", goals_next_year="",
                          digest_filename="brag-digest-2026-09-04.md")
    sections = [
        "Goals for this year",
        "Goals for next year",
        "Projects",
        "Collaboration & mentorship",
        "Design & documentation",
        "Company building",
        "What you learned",
        "Outside of work",
    ]
    positions = [text.index(s) for s in sections]
    assert positions == sorted(positions)


def test_prompt_enforces_length_and_source_fidelity_constraints():
    text = render_prompt(username="octo", goals_this_year="", goals_next_year="",
                          digest_filename="brag-digest-2026-09-04.md")
    assert "1-2 page" in text
    assert "do not invent" in text.lower() or "don't invent" in text.lower() \
        or "do not fabricate" in text.lower()
    assert "jvns.ca/blog/brag-documents" in text


def test_prompt_references_digest_filename():
    text = render_prompt(username="octo", goals_this_year="", goals_next_year="",
                          digest_filename="brag-digest-2026-09-04.md")
    assert "brag-digest-2026-09-04.md" in text


def test_prompt_includes_goals_when_provided():
    text = render_prompt(username="octo", goals_this_year="Get promoted to Associate",
                          goals_next_year="Get promoted to Prof 1",
                          digest_filename="brag-digest-2026-09-04.md")
    assert "Get promoted to Associate" in text
    assert "Get promoted to Prof 1" in text


def test_prompt_placeholders_when_goals_missing():
    text = render_prompt(username="octo", goals_this_year="", goals_next_year="",
                          digest_filename="brag-digest-2026-09-04.md")
    assert "ask me" in text.lower() or "not provided" in text.lower()
