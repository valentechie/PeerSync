import pytest

from app.ai.skillswap.matcher import score_match


def test_perfect_mutual_match_with_top_reputation_scores_100():
    result = score_match(["React"], ["SQL"], ["SQL"], ["React"], 5.0)

    assert result.score == 100
    assert (result.learn_points, result.teach_points, result.reputation_points) == (40, 40, 20)
    assert result.they_teach_you == ["SQL"]
    assert result.you_teach_them == ["React"]
    assert result.is_complementary


def test_mutual_exchange_beats_one_way_with_better_reputation():
    mutual = score_match(["React"], ["SQL"], ["SQL"], ["React"], 1.0)
    one_way = score_match(["React"], ["SQL"], ["SQL"], [], 5.0)

    assert mutual.score > one_way.score


def test_one_way_match_only_counts_that_direction():
    result = score_match([], ["SQL"], ["SQL"], ["React"], None)

    assert result.learn_points == 40
    assert result.teach_points == 0
    assert result.you_teach_them == []
    assert result.is_complementary


def test_no_overlap_is_not_complementary_even_with_reputation_points():
    result = score_match(["React"], ["SQL"], ["Docker"], ["Go"], 5.0)

    assert not result.is_complementary
    assert result.score == 20
    assert result.shared_skills == 0


def test_coverage_is_proportional_and_rounds_half_up():
    # Cubre 1 de 3 buscadas: 40/3 = 13.33 -> 13. Cubre 1 de 16: 40/16 = 2.5 -> 3.
    learn = score_match([], ["A", "B", "C"], ["A"], [], None)
    teach = score_match(["A"], [], [], ["A", *[f"S{i}" for i in range(15)]], None)

    assert learn.learn_points == 13
    assert teach.teach_points == 3


def test_new_user_gets_neutral_reputation_below_good_above_bad():
    new = score_match(["A"], ["B"], ["B"], ["A"], None)
    good = score_match(["A"], ["B"], ["B"], ["A"], 4.5)
    bad = score_match(["A"], ["B"], ["B"], ["A"], 1.0)

    assert new.reputation_points == 12
    assert bad.score < new.score < good.score


def test_skill_comparison_ignores_case():
    result = score_match(["react"], ["SQL"], ["sql"], ["REACT"], None)

    assert result.they_teach_you == ["SQL"]
    assert result.you_teach_them == ["REACT"]


def test_empty_profiles_do_not_divide_by_zero():
    result = score_match([], [], [], [], None)

    assert result.learn_points == result.teach_points == 0
    assert not result.is_complementary


def test_same_input_always_gives_same_result_regardless_of_order():
    first = score_match(["B", "A"], ["D", "C"], ["C", "D"], ["A", "B"], 4.0)
    second = score_match(["A", "B"], ["C", "D"], ["D", "C"], ["B", "A"], 4.0)

    assert first == second


@pytest.mark.parametrize("reputation", [None, 0.0, 1.0, 3.3, 5.0])
def test_score_is_always_the_sum_of_its_parts_and_within_range(reputation):
    result = score_match(["A", "B"], ["C", "D", "E"], ["C"], ["A", "Z", "Y"], reputation)

    assert result.score == result.learn_points + result.teach_points + result.reputation_points
    assert 0 <= result.score <= 100
