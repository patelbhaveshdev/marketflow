namespace MarketFlow.Core.Services;

/// <summary>
/// Exponential backoff with jitter, mirroring the retry semantics of
/// production batch schedulers (n_retrys in AutoSys JIL).
/// </summary>
public sealed class RetryPolicy(int maxRetries = 3, double baseDelaySeconds = 5, double maxDelaySeconds = 300)
{
    public int MaxRetries { get; } = maxRetries >= 0
        ? maxRetries
        : throw new ArgumentOutOfRangeException(nameof(maxRetries));

    public double BaseDelaySeconds { get; } = baseDelaySeconds;
    public double MaxDelaySeconds { get; } = maxDelaySeconds;

    public bool ShouldRetry(int attempt) => attempt <= MaxRetries;

    public RetryPolicy WithMaxRetries(int maxRetries) => new(maxRetries, BaseDelaySeconds, MaxDelaySeconds);

    public TimeSpan DelayFor(int attempt)
    {
        if (attempt < 1) throw new ArgumentOutOfRangeException(nameof(attempt));
        var exponential = BaseDelaySeconds * Math.Pow(2, attempt - 1);
        var capped = Math.Min(exponential, MaxDelaySeconds);
        var jitter = Random.Shared.NextDouble() * 0.25 * capped; // up to +25%
        return TimeSpan.FromSeconds(capped + jitter);
    }
}
