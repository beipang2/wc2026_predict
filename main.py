"""CLI entrypoint for WC2026 group stage simulator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from models.simulator import simulate_all_groups, simulate_group
from models.wildcard import simulate_wildcards
from models.knockout import simulate_knockout

console = Console()


def _load_overrides(path: str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Override file not found: {path}[/red]")
        sys.exit(1)
    return json.loads(p.read_text())


def _print_results(results: dict) -> None:
    group_id = results["group"]
    n = results["simulations"]

    console.print(f"\n[bold cyan]=== GROUP {group_id} SIMULATION RESULTS ({n:,} runs) ===[/bold cyan]\n")

    # standings table
    t = Table(show_header=True, header_style="bold")
    t.add_column("Team", min_width=16)
    t.add_column("1st", justify="right")
    t.add_column("2nd", justify="right")
    t.add_column("Advance", justify="right")
    t.add_column("xPts", justify="right")
    t.add_column("xGD", justify="right")

    sorted_teams = sorted(
        results["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True
    )
    for code, d in sorted_teams:
        t.add_row(
            d["name"],
            f"{d['p_1st']}%",
            f"{d['p_2nd']}%",
            f"[bold]{d['p_advance']}%[/bold]",
            str(d["xpts"]),
            f"{d['xgd']:+.1f}",
        )

    console.print(t)

    console.print("\n[bold]--- Most likely fixture scorelines ---[/bold]")
    for key, fx in results["fixtures"].items():
        console.print(
            f"  {fx['home']} vs {fx['away']}    →  "
            f"[yellow]{fx['most_likely_score']}[/yellow]  "
            f"({fx['frequency']}% of sims)"
        )
    console.print()


def _print_wildcards(results: dict) -> None:
    n = results["simulations"]
    console.print(f"\n[bold cyan]=== WILDCARD SELECTION ({n:,} simulations) ===[/bold cyan]")
    console.print("[dim]Best 8 of 12 third-place teams advance. Ranked by pts → GD → GF → FIFA rank.[/dim]\n")

    t = Table(show_header=True, header_style="bold")
    t.add_column("Team", min_width=20)
    t.add_column("P(3rd)", justify="right")
    t.add_column("P(wildcard)", justify="right")
    t.add_column("P(WC | 3rd)", justify="right")
    t.add_column("xPts@3rd", justify="right")
    t.add_column("xGD@3rd", justify="right")

    sorted_teams = sorted(
        results["teams"].items(), key=lambda x: x[1]["p_wildcard"], reverse=True
    )
    for i, (code, d) in enumerate(sorted_teams):
        style = "bold green" if i < 8 else "dim"
        marker = " ✓" if i < 8 else ""
        t.add_row(
            f"[{style}]{d['name']}{marker}[/{style}]",
            f"{d['p_3rd']}%",
            f"[{style}]{d['p_wildcard']}%[/{style}]",
            f"{d['p_wildcard_given_3rd']}%",
            str(d["xpts_when_3rd"]),
            f"{d['xgd_when_3rd']:+.1f}",
        )

    console.print(t)
    console.print()


RESULTS_DIR = Path("results")
DEFAULT_GROUP_STAGE_OUTPUT = RESULTS_DIR / "group_stage.json"
DEFAULT_WILDCARDS_OUTPUT = RESULTS_DIR / "wildcards.json"
DEFAULT_KNOCKOUT_OUTPUT = RESULTS_DIR / "knockout.json"


def _print_knockout(results: dict) -> None:
    n = results["simulations"]
    console.print(f"\n[bold cyan]=== KNOCKOUT STAGE ({n:,} simulations) ===[/bold cyan]\n")
    t = Table(show_header=True, header_style="bold")
    t.add_column("Team", min_width=22)
    t.add_column("R32", justify="right")
    t.add_column("R16", justify="right")
    t.add_column("QF", justify="right")
    t.add_column("SF", justify="right")
    t.add_column("Final/Win", justify="right")
    sorted_teams = sorted(results["teams"].items(), key=lambda x: x[1]["p_final"], reverse=True)
    for code, d in sorted_teams:
        t.add_row(
            d["name"],
            f"{d['p_r32']}%",
            f"{d['p_r16']}%",
            f"{d['p_qf']}%",
            f"{d['p_sf']}%",
            f"[bold]{d['p_final']}%[/bold]",
        )
    console.print(t)


@click.command()
@click.option("--group", default=None, help="Group ID to simulate (e.g. A)")
@click.option("--all", "run_all", is_flag=True, help="Simulate all 12 group stage groups")
@click.option("--wildcards", "run_wildcards", is_flag=True, help="Simulate wildcard selection (best 8 of 12 third-place teams)")
@click.option("--knockout", "run_knockout", is_flag=True, help="Simulate the knockout bracket (R32 → Final)")
@click.option("--simulations", default=10_000, show_default=True, help="Number of Monte Carlo runs")
@click.option("--output", default=None, help="Override default output path for results JSON")
@click.option("--no-save", is_flag=True, default=False, help="Skip writing results to disk")
@click.option("--overrides", default=None, help="Path to overrides JSON (team rating overrides)")
@click.option("--seed", default=None, type=int, help="Random seed for reproducibility")
def cli(group, run_all, run_wildcards, run_knockout, simulations, output, no_save, overrides, seed):
    """2026 FIFA World Cup Monte Carlo simulator."""
    override_data = _load_overrides(overrides)
    RESULTS_DIR.mkdir(exist_ok=True)

    if run_knockout:
        results = simulate_knockout(n=simulations, seed=seed)
        _print_knockout(results)
        if not no_save:
            out = Path(output) if output else DEFAULT_KNOCKOUT_OUTPUT
            out.write_text(json.dumps(results, indent=2))
            console.print(f"[green]Results written to {out}[/green]")
        return

    if run_wildcards:
        results = simulate_wildcards(n=simulations, seed=seed)
        _print_wildcards(results)
        if not no_save:
            out = Path(output) if output else DEFAULT_WILDCARDS_OUTPUT
            out.write_text(json.dumps(results, indent=2))
            console.print(f"[green]Results written to {out}[/green]")
        return

    if run_all:
        all_results = simulate_all_groups(n=simulations, overrides=override_data)
        for gid, res in all_results.items():
            _print_results(res)
        if not no_save:
            out = Path(output) if output else DEFAULT_GROUP_STAGE_OUTPUT
            out.write_text(json.dumps(all_results, indent=2))
            console.print(f"[green]Results written to {out}[/green]")
    elif group:
        results = simulate_group(
            group.upper(), n=simulations, overrides=override_data, seed=seed
        )
        _print_results(results)
        if not no_save:
            out = Path(output) if output else RESULTS_DIR / f"group_{group.upper()}.json"
            out.write_text(json.dumps(results, indent=2))
            console.print(f"[green]Results written to {out}[/green]")
    else:
        console.print("[red]Specify --group <ID>, --all, --wildcards, or --knockout[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
