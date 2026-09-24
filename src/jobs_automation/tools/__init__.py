"""V23 Agent Tools framework initialization."""

from jobs_automation.tools.action_tools import register_action_tools
from jobs_automation.tools.envelope import (
    ActionClass,
    ErrorCategory,
    PermissionContext,
    ToolRequest,
    ToolResult,
    ToolStatus,
)
from jobs_automation.tools.permission_gate import PermissionGate
from jobs_automation.tools.prep_tools import register_prep_tools
from jobs_automation.tools.read_tools import register_read_tools
from jobs_automation.tools.registry import ToolRegistry, ToolSpec
from jobs_automation.tools.runtime import ToolRuntime


def get_default_tool_registry() -> ToolRegistry:
    """Build and return a ToolRegistry populated with all standard V2.3 tools."""
    registry = ToolRegistry()
    register_read_tools(registry)
    register_prep_tools(registry)
    register_action_tools(registry)
    return registry
