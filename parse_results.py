"""Parse and display group stage + wildcard results from saved JSON files."""

from __future__ import annotations

import io
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

RESULTS_DIR = Path("results")
DEFAULT_GROUP_STAGE = RESULTS_DIR / "group_stage.json"
DEFAULT_WILDCARDS = RESULTS_DIR / "wildcards.json"


def _load_json(path: Path) -> dict:
    import json
    if not path.exists():
        console.print(f"[red]File not found: {path}  —  run main.py first.[/red]")
        raise SystemExit(1)
    return json.loads(path.read_text())


def _top2_teams(gs: dict) -> set[str]:
    """Return codes of teams most likely to finish 1st or 2nd in each group."""
    top2 = set()
    for gid, data in gs.items():
        ranked = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)
        top2.update(code for code, _ in ranked[:2])
    return top2


def show_bracket(gs: dict, wc: dict) -> None:
    """Full bracket view: 1st–4th per group, then wildcard table."""
    wc_teams = sorted(wc["teams"].items(), key=lambda x: x[1]["p_wildcard"], reverse=True)
    top2_for_wc = _top2_teams(gs)
    # top 8 wildcards excluding teams already likely to advance as 1st/2nd
    wc_set = {code for code, _ in wc_teams if code not in top2_for_wc}
    wc_set = {code for code, _ in [(c, d) for c, d in wc_teams if c not in top2_for_wc][:8]}
    n = next(iter(gs.values()))["simulations"]

    console.print(f"\n[bold cyan]══ WC 2026 BRACKET  ({n:,} simulations) ══[/bold cyan]\n")

    for gid in "ABCDEFGHIJKL":
        if gid not in gs:
            continue
        data = gs[gid]
        teams = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)

        t = Table(box=box.SIMPLE, show_header=True, header_style="bold white",
                  expand=False, padding=(0, 1))
        t.add_column(f"G{gid}", width=3)
        t.add_column("Team", width=24, no_wrap=True)
        t.add_column("1st%", justify="right", width=5)
        t.add_column("2nd%", justify="right", width=5)
        t.add_column("3rd%", justify="right", width=5)
        t.add_column("4th%", justify="right", width=5)
        t.add_column("Adv%", justify="right", width=6)

        for i, (code, d) in enumerate(teams, 1):
            pos_label = ["1st", "2nd", "3rd", "4th"][i - 1]
            is_wc = i == 3 and code in wc_set
            wc_tag = " [bold yellow]*WC[/bold yellow]" if is_wc else ""

            if i <= 2:
                style = "green"
            elif is_wc:
                style = "yellow"
            else:
                style = "dim"

            name = d['name'][:22]
            t.add_row(
                f"[{style}]{pos_label}[/{style}]",
                f"[{style}]{name}[/{style}]{wc_tag}",
                f"{d['p_1st']}",
                f"{d['p_2nd']}",
                f"{d['p_3rd']}",
                f"{d['p_4th']}",
                f"[{style}]{d['p_advance']}[/{style}]",
            )

        console.print(t)

    # Wildcard table
    n_wc = wc["simulations"]
    top2 = _top2_teams(gs)
    console.print(f"\n[bold cyan]══ WILDCARDS — best 8 of 12 third-place teams  ({n_wc:,} simulations) ══[/bold cyan]\n")

    wt = Table(box=box.SIMPLE, show_header=True, header_style="bold white",
               expand=False, padding=(0, 1))
    wt.add_column("#", width=3)
    wt.add_column("Grp", width=4)
    wt.add_column("Team", min_width=24)
    wt.add_column("P(3rd)", justify="right", width=7)
    wt.add_column("P(WC)", justify="right", width=7)
    wt.add_column("P(WC|3rd)", justify="right", width=10)
    wt.add_column("xPts@3rd", justify="right", width=9)

    valid_wc_count = 0
    separator_done = False
    for i, (code, d) in enumerate(wc_teams, 1):
        is_conflict = code in top2
        if not is_conflict:
            valid_wc_count += 1
        separator = (valid_wc_count == 8 and not is_conflict and not separator_done)
        if separator:
            separator_done = True
        if is_conflict:
            style = "strike dim"
            note = " [dim]~top2[/dim]"
        elif valid_wc_count <= 8:
            style = "bold green"
            note = "  ✓"
        else:
            style = "dim"
            note = ""
        wt.add_row(
            f"[{style}]{i}[/{style}]",
            f"[dim]{d.get('group','?')}[/dim]",
            f"[{style}]{d['name']}[/{style}]{note}",
            f"{d['p_3rd']}%",
            f"[{style}]{d['p_wildcard']}%[/{style}]",
            f"{d['p_wildcard_given_3rd']}%",
            str(d["xpts_when_3rd"]),
            end_section=separator,
        )

    console.print(wt)


def show_groups_only(gs: dict) -> None:
    import json
    n = next(iter(gs.values()))["simulations"]
    console.print(f"\n[bold cyan]══ GROUP STAGE  ({n:,} simulations) ══[/bold cyan]\n")
    for gid in "ABCDEFGHIJKL":
        if gid not in gs:
            continue
        data = gs[gid]
        teams = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)
        console.print(f"[bold]Group {gid}[/bold]")
        for i, (code, d) in enumerate(teams, 1):
            pos = ["1st", "2nd", "3rd", "4th"][i - 1]
            style = "green" if i <= 2 else "dim"
            console.print(
                f"  [{style}]{pos}  {d['name']:<22}  "
                f"Adv:{d['p_advance']:>5}%  1st:{d['p_1st']:>5}%  "
                f"2nd:{d['p_2nd']:>5}%  xPts:{d['xpts']:>5}  xGD:{d['xgd']:>+5.1f}[/{style}]"
            )
        console.print()


def show_wildcards_only(wc: dict) -> None:
    n = wc["simulations"]
    wc_teams = sorted(wc["teams"].items(), key=lambda x: x[1]["p_wildcard"], reverse=True)
    console.print(f"\n[bold cyan]══ WILDCARDS  ({n:,} simulations) ══[/bold cyan]\n")
    for i, (code, d) in enumerate(wc_teams, 1):
        style = "bold green" if i <= 8 else "dim"
        mark = "✓" if i <= 8 else " "
        console.print(
            f"  [{style}]{i:>2}. {mark}  {d['name']:<24}  "
            f"P(WC):{d['p_wildcard']:>5}%  P(WC|3rd):{d['p_wildcard_given_3rd']:>5}%  "
            f"xPts:{d['xpts_when_3rd']:>5}[/{style}]"
        )
        if i == 8:
            console.print(f"  {'─' * 65}")


DEFAULT_OUTPUT = RESULTS_DIR / "bracket.txt"
DEFAULT_KNOCKOUT = RESULTS_DIR / "knockout.json"


def show_knockout(ko: dict) -> None:
    """Display knockout stage probabilities per team."""
    n = ko["simulations"]
    teams = sorted(ko["teams"].items(), key=lambda x: x[1]["p_final"], reverse=True)

    console.print(f"\n[bold cyan]══ KNOCKOUT STAGE  ({n:,} simulations) ══[/bold cyan]\n")

    t = Table(box=box.SIMPLE, show_header=True, header_style="bold white",
              expand=False, padding=(0, 1))
    t.add_column("#", width=3)
    t.add_column("Team", width=24, no_wrap=True)
    t.add_column("R32%", justify="right", width=6)
    t.add_column("R16%", justify="right", width=6)
    t.add_column("QF%",  justify="right", width=6)
    t.add_column("SF%",  justify="right", width=6)
    t.add_column("Win%", justify="right", width=6)

    for i, (code, d) in enumerate(teams, 1):
        win = d["p_final"]
        if win >= 10:
            style = "bold green"
        elif win >= 5:
            style = "green"
        elif win >= 1:
            style = ""
        else:
            style = "dim"
        name = d["name"][:22]
        row = [
            f"[{style}]{i}[/{style}]" if style else str(i),
            f"[{style}]{name}[/{style}]" if style else name,
            f"{d['p_r32']}",
            f"{d['p_r16']}",
            f"{d['p_qf']}",
            f"{d['p_sf']}",
            f"[bold]{d['p_final']}[/bold]",
        ]
        t.add_row(*row)
        if i == 8:
            t.add_section()

    console.print(t)


@click.command()
@click.option("--groups-file", default=str(DEFAULT_GROUP_STAGE), show_default=True,
              help="Path to group stage results JSON.")
@click.option("--wildcards-file", default=str(DEFAULT_WILDCARDS), show_default=True,
              help="Path to wildcards results JSON.")
@click.option("--knockout-file", default=str(DEFAULT_KNOCKOUT), show_default=True,
              help="Path to knockout results JSON.")
@click.option("--mode", default="all",
              type=click.Choice(["all", "bracket", "groups", "wildcards", "knockout"]),
              show_default=True,
              help="all = bracket+knockout; bracket = group/wildcard view; knockout = KO only.")
@click.option("--output", default=str(DEFAULT_OUTPUT), show_default=True,
              help="Path to save plain-text output.")
def main(groups_file: str, wildcards_file: str, knockout_file: str, mode: str, output: str) -> None:
    """Display WC 2026 simulation results and save to a text file."""
    # capture output for file while also printing to terminal
    string_buf = io.StringIO()
    file_console = Console(file=string_buf, no_color=True, width=90)

    def _run(con: Console) -> None:
        global console
        _orig = console
        console = con
        if mode in ("all", "bracket"):
            gs = _load_json(Path(groups_file))
            wc = _load_json(Path(wildcards_file))
            show_bracket(gs, wc)
        if mode in ("all", "knockout"):
            ko = _load_json(Path(knockout_file))
            show_knockout(ko)
        if mode == "groups":
            gs = _load_json(Path(groups_file))
            show_groups_only(gs)
        if mode == "wildcards":
            wc = _load_json(Path(wildcards_file))
            show_wildcards_only(wc)
        console = _orig

    # print to terminal
    _run(console)
    # capture to file (no color codes)
    _run(file_console)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(string_buf.getvalue())
    console.print(f"\n[green]Saved to {out_path}[/green]")


if __name__ == "__main__":
    main()
