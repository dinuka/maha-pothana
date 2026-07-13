from app.models.review_status import ReviewStatus, compute_review_status


def test_rejected_wins_over_everything():
    assert compute_review_status(3, 3, 3, True) == ReviewStatus.REJECTED


def test_not_started():
    assert compute_review_status(0, 0, 0, False) == ReviewStatus.NOT_STARTED


def test_no_translations():
    assert compute_review_status(3, 0, 0, False) == ReviewStatus.NO_TRANSLATIONS


def test_partially_translated():
    assert compute_review_status(3, 2, 0, False) == ReviewStatus.PARTIALLY_TRANSLATED


def test_fully_translated_zero_approved():
    assert compute_review_status(3, 3, 0, False) == ReviewStatus.FULLY_TRANSLATED


def test_partially_approved():
    assert compute_review_status(3, 3, 1, False) == ReviewStatus.PARTIALLY_APPROVED


def test_fully_approved():
    assert compute_review_status(3, 3, 3, False) == ReviewStatus.FULLY_APPROVED


def test_ambiguous_state_prefers_partially_translated_over_partially_approved():
    # 3 sections: 1 approved, 1 translated-only, 1 untouched.
    # Matches both "partially translated" and "partially approved" predicates;
    # partially-translated is checked first and must win.
    assert compute_review_status(3, 2, 1, False) == ReviewStatus.PARTIALLY_TRANSLATED
