import pytest
from datetime import datetime, timezone
from commands.gerar import _month_ranges, _build_raw_content

MONTH_ABBR = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def test_month_ranges_single_month_full():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    ranges = list(_month_ranges(start, end))
    assert len(ranges) == 1
    assert ranges[0][2] == "jan"
    assert ranges[0][3] == 2026


def test_month_ranges_single_month_partial():
    start = datetime(2026, 4, 10, tzinfo=timezone.utc)
    end = datetime(2026, 4, 20, tzinfo=timezone.utc)
    ranges = list(_month_ranges(start, end))
    assert len(ranges) == 1
    assert ranges[0][2] == "abr"
    assert ranges[0][0].day == 10
    assert ranges[0][1].day == 20


def test_month_ranges_three_months():
    start = datetime(2026, 1, 15, tzinfo=timezone.utc)
    end = datetime(2026, 3, 10, tzinfo=timezone.utc)
    ranges = list(_month_ranges(start, end))
    assert len(ranges) == 3
    assert [r[2] for r in ranges] == ["jan", "fev", "mar"]
    # January: 15th to end of month
    assert ranges[0][0].day == 15
    assert ranges[0][1].month == 1
    # February: full month
    assert ranges[1][0].day == 1
    assert ranges[1][1].month == 2
    # March: 1st to 10th
    assert ranges[2][0].day == 1
    assert ranges[2][1].day == 10


def test_month_ranges_crosses_year():
    start = datetime(2025, 11, 15, tzinfo=timezone.utc)
    end = datetime(2026, 1, 10, tzinfo=timezone.utc)
    ranges = list(_month_ranges(start, end))
    assert len(ranges) == 3
    assert ranges[0][2] == "nov"
    assert ranges[0][3] == 2025
    assert ranges[1][2] == "dez"
    assert ranges[1][3] == 2025
    assert ranges[2][2] == "jan"
    assert ranges[2][3] == 2026


def test_build_raw_content_includes_prs():
    from datetime import datetime, timezone
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, tzinfo=timezone.utc)
    author_prs = {
        "repo-one": [
            {
                "id": 42,
                "title": "Add feature X",
                "description": "Adds feature X to the system",
                "source_branch": "feature/x",
                "dest_branch": "main",
                "merged_on": "2026-01-15T10:00:00+00:00",
                "link": "https://bitbucket.org/ws/repo-one/pullrequests/42",
            }
        ]
    }
    reviewed_prs = {"repo-one": []}
    content = _build_raw_content(
        "Janeiro", 2026, start, end, "retroativo",
        ["repo-one"], author_prs, reviewed_prs
    )
    assert "# Dados Brutos — Janeiro 2026" in content
    assert "## Modo: retroativo" in content
    assert "PR #42" in content
    assert "Add feature X" in content
    assert "Adds feature X" in content
    assert "feature/x → main" in content


def test_build_raw_content_shows_no_description():
    from datetime import datetime, timezone
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, tzinfo=timezone.utc)
    author_prs = {
        "repo-one": [
            {
                "id": 1, "title": "Fix bug",
                "description": None,
                "source_branch": "fix/bug",
                "dest_branch": "main",
                "merged_on": "2026-01-10T10:00:00+00:00",
                "link": "https://bitbucket.org/ws/repo-one/pullrequests/1",
            }
        ]
    }
    content = _build_raw_content(
        "Janeiro", 2026, start, end, "retroativo",
        ["repo-one"], author_prs, {"repo-one": []}
    )
    assert "sem descrição" in content
