namespace MarketFlow.Core.Models;

public sealed class JobRun
{
    public Guid RunId { get; } = Guid.NewGuid();
    public required string JobName { get; init; }
    public JobRunStatus Status { get; private set; } = JobRunStatus.Pending;
    public int Attempt { get; private set; }
    public DateTimeOffset? StartedAt { get; private set; }
    public DateTimeOffset? CompletedAt { get; private set; }
    public string? Error { get; private set; }

    public void MarkRunning()
    {
        Status = JobRunStatus.Running;
        Attempt++;
        StartedAt = DateTimeOffset.UtcNow;
    }

    public void MarkSucceeded()
    {
        Status = JobRunStatus.Succeeded;
        CompletedAt = DateTimeOffset.UtcNow;
    }

    public void MarkFailed(string error)
    {
        Status = JobRunStatus.Failed;
        Error = error;
        CompletedAt = DateTimeOffset.UtcNow;
    }
}

public enum JobRunStatus { Pending, Running, Succeeded, Failed, Skipped }
