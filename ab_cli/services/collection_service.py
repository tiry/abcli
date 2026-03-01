"""Service for batch collection of agent invocations."""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError
from ab_cli.models.collection import (
    CollectionAgent,
    CollectionMetrics,
    CollectionResult,
)
from ab_cli.models.invocation import ChatMessage, InvokeRequest, InvokeTaskRequest
from ab_cli.utils.csv_parser import parse_chat_csv
from ab_cli.utils.jsonl_handler import parse_jsonl, write_jsonl_line


class CollectionService:
    """Service for processing batch invocations and collecting results."""

    def __init__(self, client: AgentBuilderClient, retry_delay_sec: float = 1.5):
        """Initialize collection service.

        Args:
            client: Authenticated API client
            retry_delay_sec: Delay before retry (default: 1.5 seconds)
        """
        self.client = client
        self.retry_delay_sec = retry_delay_sec

    def _invoke_chat(
        self, agent_id: str, version_id: str, message: str
    ) -> tuple[dict[str, Any], int, int]:
        """Invoke chat agent and capture timing.

        Returns:
            Tuple of (response_dict, status_code, execution_time_ms)
        """
        start_time = time.perf_counter()

        request = InvokeRequest(messages=[ChatMessage(role="user", content=message)])
        response = self.client.invoke_agent(agent_id, version_id, request)

        end_time = time.perf_counter()
        execution_time_ms = int((end_time - start_time) * 1000)

        # Extract response data
        response_dict = response.model_dump()
        status_code = 200  # Successful response

        return response_dict, status_code, execution_time_ms

    def _invoke_task(
        self, agent_id: str, version_id: str, task_data: dict[str, Any]
    ) -> tuple[dict[str, Any], int, int]:
        """Invoke task agent and capture timing.

        Returns:
            Tuple of (response_dict, status_code, execution_time_ms)
        """
        start_time = time.perf_counter()

        request = InvokeTaskRequest(inputs=task_data)
        response = self.client.invoke_task(agent_id, version_id, request)

        end_time = time.perf_counter()
        execution_time_ms = int((end_time - start_time) * 1000)

        # Extract response data
        response_dict = response.model_dump()
        status_code = 200  # Successful response

        return response_dict, status_code, execution_time_ms

    def _process_single_invocation(
        self,
        agent_id: str,
        version_id: str,
        invocation_index: int,
        message_id: str,
        input_data: dict[str, Any],
        is_chat: bool,
        output_file: TextIO,
        progress_total: int,
    ) -> bool:
        """Process a single invocation with retry logic.

        Args:
            agent_id: Target agent ID
            version_id: Target version ID
            invocation_index: Zero-based index
            message_id: Message identifier
            input_data: Input to send to agent
            is_chat: True for chat, False for task
            output_file: Output file handle
            progress_total: Total number of invocations

        Returns:
            True if successful, False if failed after retry

        Raises:
            SystemExit: If invocation fails after retry
        """
        retry_count = 0

        while retry_count <= 1:  # 0 = first attempt, 1 = retry
            try:
                # Show progress
                retry_suffix = " (retry)" if retry_count > 0 else ""
                print(
                    f"Processing invocation {invocation_index + 1}/{progress_total}...{retry_suffix}",
                    file=sys.stderr,
                )

                # Invoke agent
                if is_chat:
                    message = input_data.get("message", "")
                    output, status_code, exec_time = self._invoke_chat(
                        agent_id, version_id, message
                    )
                else:
                    output, status_code, exec_time = self._invoke_task(
                        agent_id, version_id, input_data
                    )

                # Create successful result
                result = CollectionResult(
                    timestamp=datetime.utcnow(),
                    invocation_index=invocation_index,
                    message_id=message_id,
                    agent=CollectionAgent(agent_id=agent_id, version_id=version_id),
                    input=input_data,
                    output=output,
                    metrics=CollectionMetrics(
                        success=True,
                        status_code=status_code,
                        execution_time_ms=exec_time,
                        retry_count=retry_count,
                        error_message=None,
                    ),
                )

                # Write to output file
                write_jsonl_line(output_file, result.to_dict())

                return True

            except APIError as e:
                retry_count += 1

                if retry_count > 1:
                    # Failed after retry - abort
                    error_msg = str(e)
                    print(
                        f"\nERROR: Invocation failed after retry (index {invocation_index}): {error_msg}",
                        file=sys.stderr,
                    )

                    # Write failed result
                    result = CollectionResult(
                        timestamp=datetime.utcnow(),
                        invocation_index=invocation_index,
                        message_id=message_id,
                        agent=CollectionAgent(agent_id=agent_id, version_id=version_id),
                        input=input_data,
                        output=None,
                        metrics=CollectionMetrics(
                            success=False,
                            status_code=None,
                            execution_time_ms=0,
                            retry_count=retry_count - 1,
                            error_message=error_msg,
                        ),
                    )
                    write_jsonl_line(output_file, result.to_dict())

                    # Abort batch
                    raise SystemExit(1)

                # Wait before retry
                time.sleep(self.retry_delay_sec)

        return False

    def process_chat_batch(
        self,
        agent_id: str,
        version_id: str,
        csv_path: str | Path,
        output_path: str | Path,
    ) -> tuple[int, int]:
        """Process a batch of chat messages from CSV.

        Args:
            agent_id: Target agent ID
            version_id: Target version ID
            csv_path: Path to input CSV file
            output_path: Path to output JSONL file

        Returns:
            Tuple of (total_processed, failed_count)
        """
        # Create output directory if needed
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Parse inputs to get count
        inputs = list(parse_chat_csv(csv_path))
        total = len(inputs)

        failed = 0

        with open(output_path, "w", encoding="utf-8") as output_file:
            for index, chat_input in enumerate(inputs):
                input_data = {"message": chat_input.message}

                success = self._process_single_invocation(
                    agent_id=agent_id,
                    version_id=version_id,
                    invocation_index=index,
                    message_id=chat_input.message_id,
                    input_data=input_data,
                    is_chat=True,
                    output_file=output_file,
                    progress_total=total,
                )

                if not success:
                    failed += 1

        return total, failed

    def process_task_batch(
        self,
        agent_id: str,
        version_id: str,
        jsonl_path: str | Path,
        output_path: str | Path,
    ) -> tuple[int, int]:
        """Process a batch of tasks from JSONL.

        Args:
            agent_id: Target agent ID
            version_id: Target version ID
            jsonl_path: Path to input JSONL file
            output_path: Path to output JSONL file

        Returns:
            Tuple of (total_processed, failed_count)
        """
        # Create output directory if needed
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Parse inputs to get count
        inputs = list(parse_jsonl(jsonl_path))
        total = len(inputs)

        failed = 0

        with open(output_path, "w", encoding="utf-8") as output_file:
            for index, task_data in enumerate(inputs):
                message_id = str(index)

                success = self._process_single_invocation(
                    agent_id=agent_id,
                    version_id=version_id,
                    invocation_index=index,
                    message_id=message_id,
                    input_data=task_data,
                    is_chat=False,
                    output_file=output_file,
                    progress_total=total,
                )

                if not success:
                    failed += 1

        return total, failed
