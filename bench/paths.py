import re

TEST_PATH = re.compile(r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]+\.py$|_test\.(py|go)$|\.(test|spec)\.[cm]?[jt]sx?$")
TEST_FILE = re.compile(r"(^|/)test_[^/]+\.py$|_test\.(py|go)$|\.(test|spec)\.[cm]?[jt]sx?$")
CONTEXT_FILES = ("AGENTS.md", "CLAUDE.md")
CONTEXT_DIRS = (".claude", ".codex", ".agents", ".pi")
