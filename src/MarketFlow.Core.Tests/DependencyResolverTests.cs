using MarketFlow.Core.Models;
using MarketFlow.Core.Services;
using Xunit;

namespace MarketFlow.Core.Tests;

public class DependencyResolverTests
{
    private static Job J(string name, params string[] deps) =>
        new() { Name = name, Command = "echo", DependsOn = deps };

    [Fact]
    public void Resolve_OrdersDependenciesFirst()
    {
        var order = DependencyResolver.Resolve([J("load", "transform"), J("ingest"), J("transform", "ingest")]);
        var names = order.Select(j => j.Name).ToList();

        Assert.True(names.IndexOf("ingest") < names.IndexOf("transform"));
        Assert.True(names.IndexOf("transform") < names.IndexOf("load"));
    }

    [Fact]
    public void Resolve_DetectsCycle()
    {
        var ex = Assert.Throws<InvalidOperationException>(() =>
            DependencyResolver.Resolve([J("a", "b"), J("b", "a")]));
        Assert.Contains("cycle", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Resolve_ThrowsOnUnknownDependency()
    {
        Assert.Throws<InvalidOperationException>(() =>
            DependencyResolver.Resolve([J("a", "ghost")]));
    }
}
