## API Reference

### TimestampScheduler Class

#### Methods:

- `add_job(job_id: str, timestamps: List[int], func: Callable, *args, **kwargs) -> bool`
  - Add a new job to the scheduler
  - Returns `True` if successful, `False` if job ID already exists

- `pause_job(job_id: str) -> bool`
  - Pause a running job
  - Returns `True` if successful

- `resume_job(job_id: str) -> bool`
  - Resume a paused job
  - Returns `True` if successful

- `remove_job(job_id: str) -> bool`
  - Remove a job from the scheduler
  - Returns `True` if successful

- `get_job_status(job_id: str) -> Optional[Dict]`
  - Get detailed status of a job
  - Returns status dictionary or `None` if job doesn't exist

- `list_jobs() -> List[str]`
  - Get list of all job IDs

- `get_all_statuses() -> Dict[str, Dict]`
  - Get status of all jobs

- `shutdown()`
  - Cancel all jobs and cleanup

### Status Dictionary Format

```python
{
    'job_id': 'job1',
    'status': 'running',  # 'running', 'paused', 'completed', 'removed'
    'current_index': 2,
    'total_tasks': 5,
    'completed_tasks': 2,
    'elapsed_time_ms': 1500.0,
    'next_timestamp': 350
}
```


### Example usage and demonstration

```python
if __name__ == "__main__":
  import time

    def example_job(message: str, number: int, job_id: str = "unknown"):
        current_time = time.time()
        print(f"[{current_time:.3f}] Job {job_id} executed: {message} - {number}")


    # Create scheduler
    scheduler = TimestampScheduler()

    # Example
    timestamps = [0, 200, 250, 3000]
    scheduler.add_job("job1", timestamps, example_job, "Hello", 42, job_id="job1")

    print("Job added. Waiting 1 second then pausing...")
    time.sleep(1)

    # Pause the job
    scheduler.pause_job("job1")
    print("Job paused")

    # Wait 2 seconds while paused
    time.sleep(2)

    # Resume the job
    print("Resuming job...")
    scheduler.resume_job("job1")

    # Let it complete
    time.sleep(5)

    # Show final status
    status = scheduler.get_job_status("job1")
    if status:
        print(f"Final status: {status}")

    print("\n" + "=" * 50)
    print("Testing the specific scenario.")

    timestamps2 = [0, 200, 350, 600, 500, 4050, 5000]  # Note: will be sorted to [0, 200, 350, 500, 600, 4050, 5000]


    def test_job(timestamp_ms):
        current_time = time.time()
        print(f"[{current_time:.3f}] Test job executed for timestamp {timestamp_ms}ms")


    scheduler.add_job("test_job", timestamps2, test_job, "test")

    # Let it run for 300ms then pause
    time.sleep(0.3)
    scheduler.pause_job("test_job")
    print("Job paused after 300ms")

    # Wait until 4 seconds total, then resume
    time.sleep(3.7)
    print("Resuming at 4000ms...")
    scheduler.resume_job("test_job")

    # Let it complete
    time.sleep(3)

    print("Done!")
    scheduler.shutdown()
```