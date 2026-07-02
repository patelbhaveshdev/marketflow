using MarketFlow.Core.Services;
using Xunit;

namespace MarketFlow.Core.Tests;

public class RetryPolicyTests
{
    [Fact]
    public void ShouldRetry_RespectsMaxRetries()
    {
        var policy = new RetryPolicy(maxRetries: 2);
        Assert.True(policy.ShouldRetry(1));
        Assert.True(policy.ShouldRetry(2));
        Assert.False(policy.ShouldRetry(3));
    }

    [Fact]
    public void DelayFor_GrowsExponentiallyAndIsCapped()
    {
        var policy = new RetryPolicy(5, baseDelaySeconds: 1, maxDelaySeconds: 4);
        Assert.InRange(policy.DelayFor(1).TotalSeconds, 1, 1.25);
        Assert.InRange(policy.DelayFor(2).TotalSeconds, 2, 2.5);
        Assert.InRange(policy.DelayFor(10).TotalSeconds, 4, 5); // capped
    }
}
