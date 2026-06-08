"""CLI entrypoint for WC2026 group stage simulator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from models.simulator import simulate_all_groups, simulate_group

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


@click.command()
@click.option("--group", default=None, help="Group ID to simulate (e.g. A)")
@click.option("--all", "run_all", is_flag=True, help="Simulate all groups")
@click.option("--simulations", default=10_000, show_default=True, help="Number of Monte Carlo runs")
@click.option("--output", default=None, help="Write results JSON to this path")
@click.option("--overrides", default=None, help="Path to overrides JSON (team rating overrides)")
@click.option("--seed", default=None, type=int, help="Random seed for reproducibility")
def cli(group, run_all, simulations, output, overrides, seed):
    """2026 FIFA World Cup group stage Monte Carlo simulator."""
    override_data = _load_overrides(overrides)

    if run_all:
        all_results = simulate_all_groups(n=simulations, overrides=override_data)
        for gid, res in all_results.items():
            _print_results(res)
        if output:
            Path(output).write_text(json.dumps(all_results, indent=2))
            console.print(f"[green]Results written to {output}[/green]")
    elif group:
        results = simulate_group(
            group.upper(), n=simulations, overrides=override_data, seed=seed
        )
        _print_results(results)
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text(json.dumps(results, indent=2))
            console.print(f"[green]Results written to {output}[/green]")
    else:
        console.print("[red]Specify --group <ID> or --all[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
