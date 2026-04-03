"""make-cli execution commands — /executions and /incomplete-executions endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("execution")
def execution():
    """View scenario execution history and details."""
    pass


@execution.command("list")
@click.option("--scenario", "scenario_id", required=True, type=int, help="Scenario ID")
@click.option("--status", default=None,
              type=click.Choice(["success", "warning", "error"]),
              help="Filter by status")
@click.option("--from", "from_ts", default=None, type=int, help="Start timestamp (unix ms)")
@click.option("--to", "to_ts", default=None, type=int, help="End timestamp (unix ms)")
@click.option("--limit", default=20, type=int, show_default=True, help="Max results")
@click.pass_obj
def execution_list(ctx, scenario_id: int, status, from_ts, to_ts, limit: int):
    """List executions for a scenario."""
    params = {"pg[limit]": limit, "pg[sortDir]": "desc"}
    if status:
        params["status"] = status
    if from_ts:
        params["from"] = from_ts
    if to_ts:
        params["to"] = to_ts
    try:
        data = ctx.client.get(f"/scenarios/{scenario_id}/logs", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    items = data.get("scenarioLogs", data.get("executions", []))
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["Execution ID", "Status", "Started", "Duration (ms)", "Operations"],
            [[e.get("executionId"), e.get("status"), e.get("timestamp"),
              e.get("duration"), e.get("operations")] for e in items],
            title=f"Executions — Scenario #{scenario_id}",
        )


@execution.command("get")
@click.argument("scenario_id", type=int)
@click.argument("execution_id")
@click.pass_obj
def execution_get(ctx, scenario_id: int, execution_id: str):
    """Get details of a specific execution."""
    try:
        data = ctx.client.get(f"/scenarios/{scenario_id}/executions/{execution_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    ex = data.get("execution", data)
    if ctx.json_mode:
        print_json(ex)
    else:
        print_kv(ex if isinstance(ex, dict) else {"data": ex},
                 title=f"Execution {execution_id}")


@execution.command("detail")
@click.argument("scenario_id", type=int)
@click.argument("execution_id")
@click.pass_obj
def execution_detail(ctx, scenario_id: int, execution_id: str):
    """Get full module-level detail of an execution."""
    try:
        data = ctx.client.get(f"/scenarios/{scenario_id}/logs/{execution_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    detail = data.get("executionLog", data)
    if ctx.json_mode:
        print_json(detail)
    else:
        print_kv(detail if isinstance(detail, dict) else {"data": detail},
                 title=f"Execution Detail {execution_id}")


@execution.command("stop")
@click.argument("scenario_id", type=int)
@click.argument("execution_id")
@click.pass_obj
def execution_stop(ctx, scenario_id: int, execution_id: str):
    """Stop a running execution."""
    try:
        data = ctx.client.post(f"/scenarios/{scenario_id}/executions/{execution_id}/stop")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(data)
    else:
        success(f"Stopped execution {execution_id}")


@click.group("incomplete")
def incomplete():
    """Manage incomplete (failed/waiting) executions."""
    pass


@incomplete.command("list")
@click.option("--scenario", "scenario_id", required=True, type=int, help="Scenario ID")
@click.option("--limit", default=20, type=int, show_default=True)
@click.pass_obj
def incomplete_list(ctx, scenario_id: int, limit: int):
    """List incomplete executions for a scenario."""
    try:
        data = ctx.client.get(
            "/incomplete-executions",
            params={"scenarioId": scenario_id, "pg[limit]": limit},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    items = data.get("incompleteExecutions", [])
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["Execution ID", "Status", "Timestamp", "Reason"],
            [[i.get("executionId"), i.get("status"), i.get("timestamp"),
              i.get("reason", "")] for i in items],
            title=f"Incomplete Executions — Scenario #{scenario_id}",
        )


@incomplete.command("get")
@click.argument("execution_id")
@click.pass_obj
def incomplete_get(ctx, execution_id: str):
    """Get details of an incomplete execution."""
    try:
        data = ctx.client.get(f"/incomplete-executions/{execution_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    ex = data.get("incompleteExecution", data)
    if ctx.json_mode:
        print_json(ex)
    else:
        print_kv(ex if isinstance(ex, dict) else {"data": ex},
                 title=f"Incomplete Execution {execution_id}")
