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
from entitysdk.migration.tracking import ExecutionSummary


def run[ApplySettingsT: ApplySettings, RevertSettingsT: RevertSettings](
    *,
    apply: Callable[[ApplySettingsT, ExecutionSummary], None],
    apply_settings: type[ApplySettingsT] = ApplySettings,
    revert: Callable[[RevertSettingsT, ExecutionSummary], None],
    revert_settings: type[RevertSettingsT] = RevertSettings,
) -> None:
    """Build the CLI from the given functions and settings types, then run it."""
    apply_fn = apply
    revert_fn = revert

    class _Apply(apply_settings):
        """Apply the migration."""

        def cli_cmd(self: ApplySettingsT) -> None:  # type: ignore[override]
            with migration_context(self, subcommand="apply") as summary:
                apply_fn(self, summary)

    class _Revert(revert_settings):
        """Revert the migration."""

        def cli_cmd(self: RevertSettingsT) -> None:  # type: ignore[override]
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

    CliApp.run(RootSettings)
