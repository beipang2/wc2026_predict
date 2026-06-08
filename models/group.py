"""Group table management and FIFA tiebreaker logic."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TeamRecord:
    code: str
    w: int = 0
    d: int = 0
    l: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def pts(self) -> int:
        return self.w * 3 + self.d

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    @property
    def played(self) -> int:
        return self.w + self.d + self.l


class GroupTable:
    def __init__(self, team_codes: list[str]):
        self.records: dict[str, TeamRecord] = {c: TeamRecord(c) for c in team_codes}
        # head-to-head results: h2h[a][b] = (pts_a, gf_a, ga_a) in matches between a and b
        self.h2h: dict[str, dict[str, tuple[int, int, int]]] = {
            c: {o: (0, 0, 0) for o in team_codes if o != c} for c in team_codes
        }

    def record_result(self, home: str, away: str, hg: int, ag: int) -> None:
        hr = self.records[home]
        ar = self.records[away]

        hr.gf += hg
        hr.ga += ag
        ar.gf += ag
        ar.ga += hg

        if hg > ag:
            hr.w += 1
            ar.l += 1
            h_pts, a_pts = 3, 0
        elif hg < ag:
            hr.l += 1
            ar.w += 1
            h_pts, a_pts = 0, 3
        else:
            hr.d += 1
            ar.d += 1
            h_pts, a_pts = 1, 1

        # update h2h
        hh, hgf, hga = self.h2h[home][away]
        self.h2h[home][away] = (hh + h_pts, hgf + hg, hga + ag)
        ah, agf, aga = self.h2h[away][home]
        self.h2h[away][home] = (ah + a_pts, agf + ag, aga + hg)

    def standings(self) -> list[str]:
        codes = list(self.records.keys())
        codes.sort(key=lambda c: self._sort_key(c, codes), reverse=True)
        return codes

    def _sort_key(self, code: str, all_codes: list[str]) -> tuple:
        r = self.records[code]
        tied = [c for c in all_codes if c != code and self.records[c].pts == r.pts]

        if not tied:
            h2h_pts = h2h_gd = h2h_gf = 0
        else:
            group = [code] + tied
            h2h_pts = sum(self.h2h[code][o][0] for o in tied)
            h2h_gd = sum(
                self.h2h[code][o][1] - self.h2h[code][o][2] for o in tied
            )
            h2h_gf = sum(self.h2h[code][o][1] for o in tied)

        # random tiebreaker (lots) — use a stable random value per code so
        # sorting is consistent within one call
        lots = random.random()

        return (r.pts, r.gd, r.gf, h2h_pts, h2h_gd, h2h_gf, lots)
