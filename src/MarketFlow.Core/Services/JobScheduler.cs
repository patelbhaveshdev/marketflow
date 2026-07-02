using System.Collections.Concurrent;
using MarketFlow.Core.Models;

namespace MarketFlow.Core.Services;

/// <summary>
/// In-memory pipeline orchestrator: resolves dependency order, executes
/// jobs, and applies retry policy on failure. Swap the executor delegate
/// for Azure Batch / Databricks Jobs API calls in production.
/// </summary>
public sealed class JobScheduler(RetryPolicy retryPolicy)
{
    private readonly ConcurrentDictionary<string, Job> _jobs = new(StringComparer.OrdinalIgnoreCase);
    private readonly ConcurrentBag<JobRun> _history = [];

    public IReadOnlyCollection<Job> Jobs => _jobs.Values.ToList();
    public IReadOnlyCollection<JobRun> History => _history.ToList();

    public bool Register(Job job) => _jobs.TryAdd(job.Name, job);

    public Job? Find(string name) => _jobs.GetValueOrDefault(name);

    /// <summary>Runs every registered job in dependency order.</summary>
    public async Task<IReadOnlyList<JobRun>> RunAllAsync(
        Func<Job, CancellationToken, Task> executor, CancellationToken ct = default)
    {
        var ordered = DependencyResolver.Resolve(_jobs.Values);
        var runs = new List<JobRun>(ordered.Count);
        var failed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var job in ordered)
        {
            var run = new JobRun { JobName = job.Name };
            _history.Add(run);
            runs.Add(run);

            if (job.DependsOn.Any(failed.Contains))
            {
                run.MarkFailed("Skipped: upstream dependency failed.");
                failed.Add(job.Name);
                continue;
            }

            await ExecuteWithRetryAsync(job, run, executor, ct);
            if (run.Status is JobRunStatus.Failed)
                failed.Add(job.Name);
        }

        return runs;
    }

    private async Task ExecuteWithRetryAsync(
        Job job, JobRun run, Func<Job, CancellationToken, Task> executor, CancellationToken ct)
    {
        var policy = retryPolicy.WithMaxRetries(job.MaxRetries);
        while (true)
        {
            try
            {
                run.MarkRunning();
                await executor(job, ct);
                run.MarkSucceeded();
                return;
            }
            catch (Exception) when (policy.ShouldRetry(run.Attempt) && !ct.IsCancellationRequested)
            {
                await Task.Delay(policy.DelayFor(run.Attempt), ct);
            }
            catch (Exception ex)
            {
                run.MarkFailed(ex.Message);
                return;
            }
        }
    }
}
