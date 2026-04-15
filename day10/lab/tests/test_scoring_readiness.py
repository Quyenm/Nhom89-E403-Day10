from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from day10.lab.instructor_quick_check import check_grading_jsonl
from day10.lab.quality.expectations import run_expectations
from day10.lab.transform.cleaning_rules import clean_rows


ROOT = Path(__file__).resolve().parents[1]


def test_clean_rows_normalizes_exported_at_and_removes_refund_migration_note() -> None:
    rows = [
        {
            "doc_id": "policy_refund_v4",
            "chunk_text": "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn (ghi chú: bản sync cũ policy-v3 - lỗi migration).",
            "effective_date": "2026-02-01",
            "exported_at": "2026-04-10 08:00:00",
        }
    ]

    cleaned, quarantine = clean_rows(rows)

    assert quarantine == []
    assert cleaned[0]["exported_at"] == "2026-04-10T08:00:00"
    assert "14 ngày làm việc" not in cleaned[0]["chunk_text"]
    assert "policy-v3" not in cleaned[0]["chunk_text"]
    assert "[cleaned: stale_refund_window]" in cleaned[0]["chunk_text"]


def test_expectations_halt_when_required_doc_missing_or_exported_at_invalid() -> None:
    cleaned_rows = [
        {
            "chunk_id": "policy_refund_v4_1",
            "doc_id": "policy_refund_v4",
            "chunk_text": "Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ xác nhận đơn.",
            "effective_date": "2026-02-01",
            "exported_at": "not-an-iso-timestamp",
        },
        {
            "chunk_id": "it_helpdesk_faq_1",
            "doc_id": "it_helpdesk_faq",
            "chunk_text": "Tài khoản bị khóa sau 5 lần đăng nhập sai liên tiếp.",
            "effective_date": "2026-02-01",
            "exported_at": "2026-04-10T08:00:00",
        },
    ]

    results, halt = run_expectations(cleaned_rows)
    by_name = {result.name: result for result in results}

    assert halt is True
    assert by_name["exported_at_iso8601"].passed is False
    assert by_name["required_doc_coverage"].passed is False


def test_check_grading_jsonl_fails_on_merit_regression() -> None:
    grading_path = ROOT / "artifacts" / "eval" / "_pytest_grading_run.jsonl"
    grading_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "id": "gq_d10_01",
            "contains_expected": False,
            "hits_forbidden": False,
            "top1_doc_matches": None,
        },
        {
            "id": "gq_d10_02",
            "contains_expected": True,
            "hits_forbidden": False,
            "top1_doc_matches": None,
        },
        {
            "id": "gq_d10_03",
            "contains_expected": True,
            "hits_forbidden": False,
            "top1_doc_matches": True,
        },
    ]
    grading_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    code, messages = check_grading_jsonl(grading_path)

    assert code == 1
    assert any(message == "MERIT_CHECK[gq_d10_01] FAIL :: refund window + không forbidden trong top-k" for message in messages)


def test_grading_questions_file_exists_and_covers_three_scored_questions() -> None:
    grading_questions_path = ROOT / "data" / "grading_questions.json"

    assert grading_questions_path.is_file()
    rows = json.loads(grading_questions_path.read_text(encoding="utf-8"))
    ids = {row["id"] for row in rows}

    assert ids == {"gq_d10_01", "gq_d10_02", "gq_d10_03"}
