using MarketFlow.Core.Models;
using MarketFlow.Core.Services;
using Xunit;

namespace MarketFlow.Core.Tests;

public class JobSchedulerTests
{
    [Fact]
    public async Task RunAll_SkipsDownstreamWhenUpstreamFails()
    {
        var scheduler = new JobScheduler(new RetryPolicy(0));
        scheduler.Register(new Job { Name = "ingest", Command = "x", MaxRetries = 0 });
        scheduler.Register(new Job { Name = "load", Command = "x", DependsOn = ["ingest"], MaxRetries = 0 });

        var runs = await scheduler.RunAllAsync((job, _) =>
            job.Name == "ingest" ? throw new InvalidOperationException("boom") : Task.CompletedTask);

        Assert.Equal(JobRunStatus.Failed, runs.Single(r => r.JobName == "ingest").Status);
        Assert.Equal(JobRunStatus.Failed, runs.Single(r => r.JobName == "load").Status);
        Assert.Contains("upstream", runs.Single(r => r.JobName == "load").Error);
    }

    [Fact]
    public async Task RunAll_RetriesThenSucceeds()
    {
        var scheduler = new JobScheduler(new RetryPolicy(2, baseDelaySeconds: 0.01));
        scheduler.Register(new Job { Name = "flaky", Command = "x", MaxRetries = 2 });

        var attempts = 0;
        var runs = await scheduler.RunAllAsync((_, _) =>
            ++attempts < 2 ? throw new TimeoutException() : Task.CompletedTask);

        Assert.Equal(JobRunStatus.Succeeded, runs.Single().Status);
        Assert.Equal(2, runs.Single().Attempt);
    }
}
