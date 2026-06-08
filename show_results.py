"""Display group stage simulation results with placement commentary."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

COMMENTS = {
    # p_advance thresholds → comment template
    # Called as comment(rank, name, p_advance, p_1st, p_2nd)
}


def _placement_comment(rank: int, name: str, p_advance: float, p_1st: float, p_2nd: float) -> str:
    if rank == 1:
        if p_advance >= 85:
            return f"Heavy favourite to top the group — {p_advance}% chance of advancing, leads {p_1st}% of sims."
        elif p_advance >= 75:
            return f"Clear group leader in {p_1st}% of sims. Advancing in {p_advance}% — comfortable but not locked in."
        elif p_advance >= 60:
            return f"Narrow group leader ({p_1st}% to finish 1st). Tight group — only {p_advance}% chance of advancing."
        else:
            return f"Slight edge for 1st ({p_1st}%) but this group is wide open. Advances just {p_advance}% of the time."

    elif rank == 2:
        gap = p_advance - (100 - p_advance)
        if p_advance >= 70:
            return f"Solid 2nd-place contender, advances in {p_advance}% of sims. Finishes 2nd in {p_2nd}%."
        elif p_advance >= 55:
            return f"Likely through but not certain — {p_advance}% advance rate. Finishes 2nd in {p_2nd}% of sims."
        elif p_advance >= 45:
            return f"Slight favourite to advance ({p_advance}%) but genuinely in danger. 2nd in {p_2nd}% of sims."
        else:
            return f"Ranked 2nd but only advances {p_advance}% of the time — elimination is the more likely outcome."

    elif rank == 3:
        if p_advance >= 40:
            return f"Realistically in contention — {p_advance}% advance rate despite 3rd place ranking. Wildcard hope."
        elif p_advance >= 25:
            return f"Unlikely but not impossible. Advances in {p_advance}% of sims — needs results to go their way."
        else:
            return f"Almost certainly going home. Just {p_advance}% chance of advancing, finishing 3rd in majority of sims."

    else:  # rank 4
        if p_advance >= 20:
            return f"Heavy underdog but {p_advance}% is not nothing — an upset or two could keep them alive."
        elif p_advance >= 10:
            return f"Likely group-stage exit. Advances in only {p_advance}% of sims."
        else:
            return f"Almost certain elimination — just {p_advance}% advance probability. Group stage likely their ceiling."


def show_group(group_id: str, data: dict) -> None:
    n = data["simulations"]
    teams = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)

    console.print(f"\n[bold cyan]GROUP {group_id}[/bold cyan]  [dim]({n:,} simulations)[/dim]")

    table = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold white",
        expand=False,
        padding=(0, 1),
    )
    table.add_column("Pos", justify="center", width=4)
    table.add_column("Team", min_width=22)
    table.add_column("Advance", justify="right", width=9)
    table.add_column("1st", justify="right", width=7)
    table.add_column("2nd", justify="right", width=7)
    table.add_column("xPts", justify="right", width=6)
    table.add_column("xGD", justify="right", width=6)

    rows = []
    for rank, (code, d) in enumerate(teams, 1):
        p_adv = d["p_advance"]
        p_1st = d["p_1st"]
        p_2nd = d["p_2nd"]
        comment = _placement_comment(rank, d["name"], p_adv, p_1st, p_2nd)

        if rank <= 2:
            adv_style = "bold green" if p_adv >= 65 else "green" if p_adv >= 50 else "yellow"
        else:
            adv_style = "yellow" if p_adv >= 35 else "dim"

        pos_icon = {1: "🥇", 2: "🥈", 3: "3rd", 4: "4th"}.get(rank, str(rank))

        table.add_row(
            pos_icon,
            d["name"],
            f"[{adv_style}]{p_adv}%[/{adv_style}]",
            f"{p_1st}%",
            f"{p_2nd}%",
            str(d["xpts"]),
            f"{d['xgd']:+.1f}",
        )
        rows.append((pos_icon, d["name"], comment))

    console.print(table)

    for pos_icon, name, comment in rows:
        console.print(f"  {pos_icon} [bold]{name}:[/bold] [dim]{comment}[/dim]")
    console.print()

    # Fixture scorelines
    console.print("  [bold]Most likely scorelines:[/bold]")
    for key, fx in data["fixtures"].items():
        console.print(
            f"    {fx['home']} vs {fx['away']}  →  "
            f"[yellow]{fx['most_likely_score']}[/yellow]  "
            f"[dim]({fx['frequency']}% of sims)[/dim]"
        )
    console.print()


@click.command()
@click.option("--group", default=None, help="Single group to show (e.g. A). Omit for all.")
@click.option("--results-dir", default="results", show_default=True, help="Path to results directory.")
def main(group: str | None, results_dir: str) -> None:
    """Show WC2026 group stage simulation results with commentary."""
    rdir = Path(results_dir)

    if group:
        groups = [group.upper()]
    else:
        groups = list("ABCDEFGHIJKL")

    for gid in groups:
        path = rdir / f"group_{gid}.json"
        if not path.exists():
            console.print(f"[red]No results file for group {gid} — run main.py first.[/red]")
            continue
        data = json.loads(path.read_text())
        show_group(gid, data)


if __name__ == "__main__":
    main()
