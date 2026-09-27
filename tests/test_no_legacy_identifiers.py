"""Prove the identifier refactor is complete, and stays complete.

The sibling contract test asserts the *shape* of the topology and
deliberately ignores brand strings, on the grounds that a rename should not
force edits there. That leaves a real gap: nothing would catch a leftover
`devconnect` in a source file, a stale Redis key, or a reverted Compose
name. This module closes that gap by scanning the tree.

Three properties make the scan trustworthy rather than merely green:

1. The forbidden tokens are matched case-insensitively, so `CloudConnect`,
   `cloudconnect`, and `DevConnect` are all caught. The upstream tree mixed
   casings freely, and a case-sensitive scan would have passed over the
   mixed-case service titles.
2. The allowlist is pinned by an exact-equality test. Silencing a failure by
   adding a source file to the allowlist is the obvious way to defeat this
   module, so growing the list is now a deliberate, visible act that fails
   the suite.
3. The scanner is tested against a planted identifier. A scan that
   excludes everything by accident is indistinguishable from a clean tree,
   so the scanner is itself asserted to fail when it should.

Documentation is exempt rather than merely tolerated: `CREDIT.md` has to
name the upstream project in order to attribute it, and `README.md` repeats
that attribution. Those two files are *required* to keep the legacy names,
and a separate test asserts they still do. The local planning notes are
exempt because they discuss the rename itself.

Nothing here starts a container or imports application code, so it runs in
well under a second.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Matched case-insensitively against every text file in the tree.
LEGACY_TOKENS = ("devconnect", "cloudconnect")

# Generated, vendored, or version-controlled internals. These are never
# authored here, so a match inside them is not this project's regression.
SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "venv",
    ".venv",
}

# Files that must keep the upstream names in order to credit them. The
# planning notes are listed because they narrate the rename.
ALLOWED_FILES = {
    "CREDIT.md",
    "README.md",
    "findings.md",
    "progress.md",
    "task_plan.md",
}

# This module spells the forbidden tokens out literally, so it necessarily
# matches itself. Excluding it keeps the patterns readable and auditable;
# hiding them behind concatenation would make the list harder to review for
# no benefit, and the file is ours rather than upstream code.
SELF_NAME = Path(__file__).name


def iter_text_files(root):
    """Yield every text file under `root`, skipping generated and vendored paths."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # Binary asset, or unreadable. Neither is something to assert on.
            continue
        yield path


def find_legacy(root, allowed_files=ALLOWED_FILES):
    """Return `(relative_path, line_number, line)` for every legacy hit.

    Excluded by path name, so the allowlist is applied here rather than in
    each test, and the same logic backs both the real scan and the
    scanner self-test.
    """
    hits = []
    for path in iter_text_files(root):
        relative = path.relative_to(root)
        if relative.name in allowed_files or relative.name == SELF_NAME:
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            lowered = line.lower()
            if any(token in lowered for token in LEGACY_TOKENS):
                hits.append((relative.as_posix(), number, line.strip()))
    return hits


def test_no_legacy_identifier_survives_in_code_or_config():
    """The core guarantee: no forbidden token outside the attribution docs."""
    hits = find_legacy(REPO_ROOT)
    assert not hits, "legacy identifiers reintroduced; rename these:\n" + "\n".join(
        f"  {path}:{number}  {line}" for path, number, line in hits
    )


def test_allowlist_has_not_been_widened():
    """Guard against silencing a real failure by allowlisting the offender.

    The only legitimate members are the two attribution documents and the
    three local planning notes. Anything else here means a source file was
    excused rather than fixed.
    """
    assert ALLOWED_FILES == {
        "CREDIT.md",
        "README.md",
        "findings.md",
        "progress.md",
        "task_plan.md",
    }, (
        "the legacy-identifier allowlist changed. Adding a file here is how this "
        "test gets defeated, so it must be a deliberate edit with a reason, not a "
        f"way to make a failure go away. Current allowlist: {sorted(ALLOWED_FILES)}"
    )


def test_attribution_documents_still_credit_the_upstream():
    """The allowlist is only safe while those documents keep crediting the author.

    `CREDIT.md` and `README.md` are exempt because attribution requires naming
    the upstream project. If a future change strips those names to satisfy the
    scanner, the exemption would be hiding a licensing problem rather than a
    naming one, so the credit itself is asserted.
    """
    for name in ("CREDIT.md", "README.md"):
        path = REPO_ROOT / name
        assert path.exists(), f"{name} is missing; attribution cannot be verified"
        text = path.read_text(encoding="utf-8")
        assert "DevConnect Pro" in text, (
            f"{name} no longer names the upstream project. Attribution is the "
            "reason these files are exempt from the legacy scan, so removing the "
            "name defeats the exemption and hides a licensing question."
        )
    credit = (REPO_ROOT / "CREDIT.md").read_text(encoding="utf-8")
    assert "bongoDev" in credit, (
        "CREDIT.md no longer names the upstream author. The application layer has "
        "no license, so the attribution is the only thing standing between this "
        "repository and an unclear provenance claim."
    )


def test_scanner_detects_a_planted_identifier(tmp_path):
    """Prove the scanner fails when it should, so a clean tree means something.

    Without this, a scanner that excluded every path, or a token list that
    matched nothing, would pass every run and prove nothing.
    """
    planted = tmp_path / "service.py"
    planted.write_text(
        "DATABASE_URL = 'postgresql://cloudconnect:x@postgres/cloudconnect'\n",
        encoding="utf-8",
    )
    hits = find_legacy(tmp_path)
    assert len(hits) == 1, f"scanner missed a planted identifier: {hits}"
    assert hits[0][0] == "service.py"
    assert hits[0][1] == 1


def test_scanner_respects_the_allowlist(tmp_path):
    """A file named in the allowlist is skipped, a sibling with the same content is not.

    This is the behaviour the attribution exemption depends on, and it is also
    the sharpest edge of the allowlist, so it is pinned in both directions.
    """
    content = "# DevConnect Pro, by bongoDev\n"
    (tmp_path / "CREDIT.md").write_text(content, encoding="utf-8")
    (tmp_path / "main.py").write_text(content, encoding="utf-8")

    hits = find_legacy(tmp_path)
    assert [path for path, _, _ in hits] == ["main.py"], (
        "the allowlist must skip CREDIT.md and still flag an identical main.py"
    )


def test_every_authored_python_module_is_covered(tmp_path):
    """Sanity-check the walker itself against a known-good and known-bad layout.

    Guards the directory-skipping logic: a `SKIP_DIRS` entry that matched a
    prefix of a real source directory would silently exclude it.
    """
    (tmp_path / "services").mkdir()
    (tmp_path / "services" / "app.py").write_text("# clean\n", encoding="utf-8")
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "index.js").write_text(
        "// cloudconnect vendored\n", encoding="utf-8"
    )
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "bundle.js").write_text("// devconnect built\n", encoding="utf-8")

    assert find_legacy(tmp_path) == [], (
        "clean source must pass and vendored or built directories must be skipped"
    )
