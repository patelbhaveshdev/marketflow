"""Unit tests for the JIL migration tool (pytest)."""
from jil2pipeline import parse_jil, validate

SAMPLE = """
/* comment */
insert_job: JOB_A
command: echo a
n_retrys: 2
priority: 1

insert_job: JOB_B
command: echo b
condition: s(JOB_A)
start_times: "06:00"
"""


def test_parses_jobs_and_dependencies():
    jobs = parse_jil(SAMPLE)
    assert [j["name"] for j in jobs] == ["JOB_A", "JOB_B"]
    assert jobs[0]["maxRetries"] == 2
    assert jobs[0]["priority"] == "Critical"
    assert jobs[1]["dependsOn"] == ["JOB_A"]
    assert jobs[1]["startTime"] == "06:00:00"


def test_validate_flags_unknown_dependency():
    jobs = parse_jil("insert_job: X\ncommand: c\ncondition: s(GHOST)\n")
    assert validate(jobs) == ["X: unknown dependency 'GHOST'"]


def test_validate_flags_missing_command():
    jobs = parse_jil("insert_job: Y\n")
    assert validate(jobs) == ["Y: missing command"]
