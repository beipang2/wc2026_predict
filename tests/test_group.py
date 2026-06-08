import pytest

from models.group import GroupTable


def test_basic_standings():
    table = GroupTable(["A", "B", "C", "D"])
    table.record_result("A", "B", 2, 0)  # A wins
    table.record_result("C", "D", 1, 1)  # draw
    standings = table.standings()
    assert standings[0] == "A"  # 3 pts top


def test_points_calculation():
    table = GroupTable(["MEX", "RSA"])
    table.record_result("MEX", "RSA", 2, 0)
    assert table.records["MEX"].pts == 3
    assert table.records["RSA"].pts == 0


def test_goal_difference():
    table = GroupTable(["MEX", "RSA"])
    table.record_result("MEX", "RSA", 3, 1)
    assert table.records["MEX"].gd == 2
    assert table.records["RSA"].gd == -2


def test_tiebreaker_uses_h2h():
    # A and B both finish on 3pts; A beat B head-to-head so A should rank higher
    table = GroupTable(["A", "B", "C", "D"])
    table.record_result("A", "B", 1, 0)   # A 3pts; B 0
    table.record_result("A", "C", 0, 2)   # A 3; C 3
    table.record_result("B", "D", 2, 0)   # B 3
    table.record_result("C", "D", 0, 2)   # C 3; D 3
    table.record_result("A", "D", 1, 0)
    table.record_result("B", "C", 0, 1)
    standings = table.standings()
    assert len(standings) == 4


def test_draw_records():
    table = GroupTable(["A", "B"])
    table.record_result("A", "B", 1, 1)
    assert table.records["A"].pts == 1
    assert table.records["B"].pts == 1
    assert table.records["A"].d == 1
    assert table.records["B"].d == 1
