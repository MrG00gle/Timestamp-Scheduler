"""
// Copyright (C) 2025 Matsvei Kuzmiankou
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public
// License as published by the Free Software Foundation; either
// version 3 of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, write to the Free Software Foundation,
// Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import threading
import time
from typing import List, Callable, Any, Optional, Dict
from .data.JobStatus import JobStatus
from .data.JobExecution import JobExecution


class Job:
    """Represents a scheduled job with pause/resume capability"""

    def __init__(self, job_id: str, timestamps: List[int], func: Callable, args: tuple = (), kwargs: dict = None):
        self.job_id = job_id
        self.timestamps = sorted(timestamps)  # Sort timestamps
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}

        # Execution tracking
        self.executions = [JobExecution(ts) for ts in self.timestamps]
        self.current_index = 0

        # State management
        self.status = JobStatus.RUNNING
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0.0

        # Threading
        self.thread = None
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self._lock = threading.RLock()

    def start(self):
        """Start executing the job"""
        with self._lock:
            if self.thread and self.thread.is_alive():
                return False

            self.start_time = time.time()
            self.cancel_event.clear()
            self.pause_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            return True

    def _run(self):
        """Main execution loop"""
        try:
            while self.current_index < len(self.executions):
                if self.cancel_event.is_set():
                    break

                # Handle pause
                if self.pause_event.is_set():
                    with self._lock:
                        if self.status == JobStatus.RUNNING:
                            self.status = JobStatus.PAUSED
                            self.pause_time = time.time()

                    # Wait until unpaused or cancelled
                    while self.pause_event.is_set() and not self.cancel_event.is_set():
                        time.sleep(0.01)

                    with self._lock:
                        if self.status == JobStatus.PAUSED and not self.cancel_event.is_set():
                            self.total_pause_duration += time.time() - self.pause_time
                            self.status = JobStatus.RUNNING

                if self.cancel_event.is_set():
                    break

                execution = self.executions[self.current_index]
                if execution.executed:
                    self.current_index += 1
                    continue

                # Calculate when to execute
                target_time = execution.timestamp / 1000.0  # Convert to seconds
                elapsed_real_time = time.time() - self.start_time
                elapsed_execution_time = elapsed_real_time - self.total_pause_duration

                if elapsed_execution_time < target_time:
                    wait_time = target_time - elapsed_execution_time
                    if wait_time > 0:
                        # Wait with cancellation check
                        end_wait_time = time.time() + wait_time
                        while time.time() < end_wait_time and not self.cancel_event.is_set() and not self.pause_event.is_set():
                            time.sleep(min(0.01, end_wait_time - time.time()))

                if self.cancel_event.is_set() or self.pause_event.is_set():
                    continue

                # Execute the job in a separate thread
                execution_thread = threading.Thread(
                    target=self._execute_job,
                    args=(execution,),
                    daemon=True
                )
                execution_thread.start()

                execution.executed = True
                self.current_index += 1

            # Mark as completed if not cancelled
            with self._lock:
                if self.status != JobStatus.REMOVED:
                    self.status = JobStatus.COMPLETED

        except Exception as e:
            print(f"Error in job {self.job_id}: {e}")

    def _execute_job(self, execution: JobExecution):
        """Execute the actual job function"""
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            print(f"Error executing job {self.job_id} at timestamp {execution.timestamp}: {e}")

    def pause(self) -> bool:
        """Pause the job"""
        with self._lock:
            if self.status == JobStatus.RUNNING:
                self.pause_event.set()
                return True
            return False

    def resume(self) -> bool:
        """Resume the job"""
        with self._lock:
            if self.status == JobStatus.PAUSED or self.pause_event.is_set():
                self.pause_event.clear()
                return True
            return False

    def cancel(self):
        """Cancel the job"""
        with self._lock:
            self.status = JobStatus.REMOVED
            self.cancel_event.set()
            self.pause_event.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get current job status"""
        with self._lock:
            elapsed_time = 0
            if self.start_time:
                elapsed_time = (time.time() - self.start_time - self.total_pause_duration) * 1000

            return {
                'job_id': self.job_id,
                'status': self.status.value,
                'current_index': self.current_index,
                'total_tasks': len(self.executions),
                'completed_tasks': sum(1 for ex in self.executions if ex.executed),
                'elapsed_time_ms': elapsed_time,
                'next_timestamp': self.timestamps[self.current_index] if self.current_index < len(
                    self.timestamps) else None
            }
