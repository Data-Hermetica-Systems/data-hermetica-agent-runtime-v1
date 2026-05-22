from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from state import AgentRuntimeState
from tools.node_script_tool import run_node_script


def main() -> None:
    console = Console()

    repo_root = Path(__file__).resolve().parents[2]

    state = AgentRuntimeState(project_root=str(repo_root))
    state.add_audit_event(
        event_type="runtime_started",
        message="Initialized Data Hermetica Agent Runtime v1 scaffold.",
        details={"project_root": str(repo_root)},
    )

    console.print(
        Panel.fit(
            "[bold]Data Hermetica Agent Runtime v1[/bold]\n"
            "Scaffold startup check completed.\n"
            f"Run ID: {state.run_id}\n"
            f"Project root: {state.project_root}",
            title="Agent Runtime",
        )
    )

    console.print("[green]State model import: OK[/green]")
    console.print("[green]Node script tool import: OK[/green]")
    console.print("[yellow]No graph, LLM, Qdrant, Dataverse, or Power Platform integration is active yet.[/yellow]")

    state.finish("completed")
    console.print(f"[green]Final status: {state.status}[/green]")


if __name__ == "__main__":
    main()
