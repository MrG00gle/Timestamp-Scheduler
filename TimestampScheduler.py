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
from typing import List, Callable, Any, Optional, Dict
from .Job import Job
import bisect


class TimestampScheduler:
    """Advanced scheduler with pause/resume functionality"""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._lock = threading.RLock()

    def add_job(self, job_id: str, timestamps: List[int], func: Callable, *args, **kwargs) -> bool:
        """
        Add a job to the scheduler

        Args:
            job_id: Unique identifier for the job
            timestamps: List of timestamps in milliseconds when to execute the job
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            True if job was added successfully, False if job with this ID already exists
        """
        with self._lock:
            if job_id in self.jobs:
                return False

            job = Job(job_id, timestamps, func, args, kwargs)
            self.jobs[job_id] = job
            job.start()
            return True

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a job

        Args:
            job_id: ID of the job to pause

        Returns:
            True if job was paused successfully, False if job doesn't exist or can't be paused
        """
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                return job.pause()
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job

        Args:
            job_id: ID of the job to resume

        Returns:
            True if job was resumed successfully, False if job doesn't exist or can't be resumed
        """
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                return job.resume()
            return False

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler

        Args:
            job_id: ID of the job to remove

        Returns:
            True if job was removed successfully, False if job doesn't exist
        """
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                job.cancel()
                del self.jobs[job_id]
                return True
            return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job

        Args:
            job_id: ID of the job

        Returns:
            Dictionary with job status information, or None if job doesn't exist
        """
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                return job.get_status()
            return None

    def list_jobs(self) -> List[str]:
        """
        Get a list of all job IDs

        Returns:
            List of job IDs
        """
        with self._lock:
            return list(self.jobs.keys())

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all jobs

        Returns:
            Dictionary mapping job IDs to their status information
        """
        with self._lock:
            return {job_id: job.get_status() for job_id, job in self.jobs.items()}

    def shutdown(self):
        """Shutdown the scheduler and cancel all jobs"""
        with self._lock:
            for job in self.jobs.values():
                job.cancel()
            self.jobs.clear()
