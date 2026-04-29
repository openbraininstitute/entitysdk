"""CLI entry point: builds the CLI from user-provided functions and settings types."""

from collections.abc import Callable

from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from entitysdk.migration.context import migration_context
from entitysdk.migration.settings import ApplySettings, RevertSettings


def run(
    *,
    apply: Callable[..., None],
    apply_settings: type[ApplySettings] = ApplySettings,
    revert: Callable[..., None],
    revert_settings: type[RevertSettings] = RevertSettings,
    cli_args: list[str] | None = None,
) -> None:
    """Build a CLI with ``apply`` and ``revert`` subcommands, then run it.

    The CLI is constructed dynamically from the provided callback functions and
    their associated settings types, which are exposed as CLI arguments.

    Args:
        apply: Callback invoked for the ``apply`` subcommand.
            Receives the parsed settings instance and an ExecutionSummary.
        apply_settings: Settings class for the ``apply`` subcommand.
            Must be a subclass of ApplySettings.
        revert: Callback invoked for the ``revert`` subcommand.
            Receives the parsed settings instance and an ExecutionSummary.
        revert_settings: Settings class for the ``revert`` subcommand.
            Must be a subclass of RevertSettings.
        cli_args: Explicit CLI arguments. If None, sys.argv is used.
    """
    apply_fn = apply
    revert_fn = revert

    class _Apply(apply_settings):  # type: ignore[misc, valid-type]
        """Apply the migration."""

        def cli_cmd(self) -> None:
            with migration_context(self, subcommand="apply") as summary:
                apply_fn(self, summary)

    class _Revert(revert_settings):  # type: ignore[misc, valid-type]
        """Revert the migration."""

        def cli_cmd(self) -> None:
            with migration_context(self, subcommand="revert") as summary:
                revert_fn(self, summary)

    class RootSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            env_nested_delimiter="__",
            nested_model_default_partial_update=True,
            case_sensitive=False,
            cli_parse_args=True,
            cli_avoid_json=True,
            cli_implicit_flags=True,
            cli_kebab_case=True,
            cli_shortcuts={
                "environment": "e",
            },
        )

        apply: CliSubCommand[_Apply]
        revert: CliSubCommand[_Revert]

        def cli_cmd(self) -> None:
            CliApp.run_subcommand(self)

    CliApp.run(RootSettings, cli_args=cli_args)
