"""Parser for Home Assistant automation YAML files."""

import logging
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class AutomationParser:
    """Parser for Home Assistant automation YAML files."""

    @staticmethod
    def parse_automation_file(content: str) -> List[Dict[str, Any]]:
        """
        Parse a YAML file containing Home Assistant automations.

        This is a best-effort parser that extracts automation metadata.
        It handles various YAML structures gracefully.

        Args:
            content: YAML file content as string

        Returns:
            List of automation dictionaries with extracted metadata including line numbers
        """
        automations = []

        try:
            # Parse YAML content with line numbers
            # First, use compose to get the document tree with line info
            try:
                root_node = yaml.compose(content)
            except Exception as e:
                logger.warning(f"Could not compose YAML for line tracking: {e}")
                root_node = None

            # Parse YAML content normally for data extraction
            data = yaml.safe_load(content)

            if data is None:
                logger.warning("Empty YAML content")
                return automations

            # Handle different YAML structures
            automations_list = []
            automation_nodes = []

            if isinstance(data, list):
                # Direct list of automations
                automations_list = data
                if root_node and isinstance(root_node, yaml.SequenceNode):
                    automation_nodes = root_node.value
            elif isinstance(data, dict):
                # Could be wrapped in a key, or a single automation
                if "automation" in data:
                    automations_list = data["automation"]
                    if not isinstance(automations_list, list):
                        automations_list = [automations_list]
                        if root_node and isinstance(root_node, yaml.MappingNode):
                            for key_node, value_node in root_node.value:
                                if (
                                    hasattr(key_node, "value")
                                    and key_node.value == "automation"
                                ):
                                    automation_nodes = (
                                        [value_node]
                                        if not isinstance(value_node, yaml.SequenceNode)
                                        else value_node.value
                                    )
                                    break
                    else:
                        if root_node and isinstance(root_node, yaml.MappingNode):
                            for key_node, value_node in root_node.value:
                                if (
                                    hasattr(key_node, "value")
                                    and key_node.value == "automation"
                                ):
                                    if isinstance(value_node, yaml.SequenceNode):
                                        automation_nodes = value_node.value
                                    break
                else:
                    # Treat the whole dict as a single automation
                    automations_list = [data]
                    if root_node:
                        automation_nodes = [root_node]
            else:
                logger.warning(f"Unexpected YAML structure: {type(data)}")
                return automations

            # Extract metadata from each automation
            for idx, auto in enumerate(automations_list):
                if not isinstance(auto, dict):
                    logger.warning(f"Skipping non-dict automation at index {idx}")
                    continue

                # Get line numbers from corresponding node
                start_line = None
                end_line = None
                if idx < len(automation_nodes):
                    node = automation_nodes[idx]
                    if hasattr(node, "start_mark") and hasattr(node, "end_mark"):
                        # Line numbers are 0-indexed in yaml, add 1 for 1-indexed
                        # start_mark.line points to the first line (0-indexed)
                        # end_mark.line points to the line after the last line (0-indexed)
                        # So end_mark.line is already one past the end in 0-indexed terms
                        start_line = node.start_mark.line + 1
                        end_line = (
                            node.end_mark.line
                        )  # Converting 0-indexed 'line after last' to 1-indexed gives us the actual last line

                parsed = AutomationParser._parse_single_automation(
                    auto, start_line, end_line
                )
                if parsed:
                    automations.append(parsed)

            logger.info("Parsed %d automations from YAML", len(automations))

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing automations: {e}")

        return automations

    @staticmethod
    def _parse_single_automation(
        automation: Dict[str, Any],
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a single automation dictionary.

        Args:
            automation: Dictionary representing one automation
            start_line: Starting line number in source file (1-indexed)
            end_line: Ending line number in source file (1-indexed)

        Returns:
            Parsed automation metadata, or None if invalid
        """
        try:
            # Extract alias/name (required for meaningful display)
            alias = (
                automation.get("alias")
                or automation.get("name")
                or automation.get("id")
            )

            # Extract description
            description = automation.get("description", "")

            # Extract trigger types (best effort)
            # Home Assistant supports both 'trigger' and 'triggers' keys
            triggers = automation.get("triggers") or automation.get("trigger", [])
            trigger_types = AutomationParser._extract_trigger_types(triggers)

            # Extract blueprint information
            blueprint_info = AutomationParser._extract_blueprint_info(automation)

            # Extract action calls (services used)
            # Home Assistant supports both 'action' and 'actions' keys
            actions = automation.get("actions") or automation.get("action", [])
            action_calls = AutomationParser._extract_action_calls(actions)

            return {
                "alias": alias,
                "description": description,
                "trigger_types": trigger_types,
                "blueprint_path": (
                    blueprint_info.get("path") if blueprint_info else None
                ),
                "blueprint_input": (
                    blueprint_info.get("input") if blueprint_info else None
                ),
                "action_calls": action_calls,
                "start_line": start_line,
                "end_line": end_line,
            }

        except Exception as e:
            logger.warning(f"Error parsing single automation: {e}")
            return None

    @staticmethod
    def _extract_trigger_types(triggers: Any) -> List[str]:
        """
        Extract trigger types from automation triggers.

        Triggers can be a single dict or a list of dicts.
        Each trigger typically has a 'platform' key (older format) or 'trigger' key (newer format).

        Args:
            triggers: Trigger configuration (dict or list)

        Returns:
            List of unique trigger types
        """
        trigger_types = []

        try:
            # Normalize to list
            if isinstance(triggers, dict):
                triggers = [triggers]
            elif not isinstance(triggers, list):
                return trigger_types

            # Extract platform/trigger from each trigger
            for trigger in triggers:
                if isinstance(trigger, dict):
                    # Try 'trigger' key first (newer format), then 'platform' (older format)
                    trigger_type = trigger.get("trigger") or trigger.get("platform")
                    if trigger_type and trigger_type not in trigger_types:
                        trigger_types.append(trigger_type)

        except Exception as e:
            logger.warning(f"Error extracting trigger types: {e}")

        return trigger_types

    @staticmethod
    def _extract_blueprint_info(automation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract blueprint information from automation.

        Automations using blueprints have a 'use_blueprint' key with path and input.

        Args:
            automation: Automation dictionary

        Returns:
            Dictionary with blueprint path and input, or None if not a blueprint
        """
        try:
            use_blueprint = automation.get("use_blueprint")
            if use_blueprint and isinstance(use_blueprint, dict):
                return {
                    "path": use_blueprint.get("path", ""),
                    "input": use_blueprint.get("input", {}),
                }
        except Exception as e:
            logger.warning(f"Error extracting blueprint info: {e}")

        return None

    @staticmethod
    def _extract_action_calls(actions: Any) -> List[str]:
        """
        Extract service calls from automation actions.

        Actions can be a single dict or a list of dicts.
        Each action may have a 'service' key (older format) or 'action' key (newer format).

        Args:
            actions: Action configuration (dict or list)

        Returns:
            List of unique service calls (e.g., 'light.turn_on')
        """
        action_calls_set = set()

        try:
            # Normalize to list
            if isinstance(actions, dict):
                actions = [actions]
            elif not isinstance(actions, list):
                return []

            # Extract service calls recursively
            def extract_from_action(action: Dict[str, Any]) -> None:
                if not isinstance(action, dict):
                    return

                # Direct service call - try 'action' key first (newer format), then 'service' (older format)
                service = action.get("action") or action.get("service")
                if service:
                    action_calls_set.add(service)

                # Check for nested actions (choose, if/then/else, repeat, etc.)
                for key in ["then", "else", "sequence", "default"]:
                    nested = action.get(key)
                    if nested:
                        if isinstance(nested, list):
                            for nested_action in nested:
                                extract_from_action(nested_action)
                        elif isinstance(nested, dict):
                            extract_from_action(nested)

                # Handle choose actions
                choose = action.get("choose")
                if isinstance(choose, list):
                    for choice in choose:
                        if isinstance(choice, dict):
                            sequence = choice.get("sequence")
                            if isinstance(sequence, list):
                                for seq_action in sequence:
                                    extract_from_action(seq_action)

            for action in actions:
                extract_from_action(action)

        except Exception as e:
            logger.warning(f"Error extracting action calls: {e}")

        return list(action_calls_set)
