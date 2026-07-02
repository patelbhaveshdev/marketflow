namespace MarketFlow.Core.Models;

/// <summary>
/// A schedulable unit of work, typically migrated from a legacy
/// AutoSys JIL definition via tools/jil2pipeline.py.
/// </summary>
public sealed record Job
{
    public required string Name { get; init; }
    public string? Description { get; init; }
    public required string Command { get; init; }
    public string Machine { get; init; } = "azure-batch-pool";
    public IReadOnlyList<string> DependsOn { get; init; } = [];
    public string? Calendar { get; init; }
    public TimeOnly? StartTime { get; init; }
    public int MaxRetries { get; init; } = 3;
    public JobPriority Priority { get; init; } = JobPriority.Normal;
}

public enum JobPriority { Low, Normal, High, Critical}
