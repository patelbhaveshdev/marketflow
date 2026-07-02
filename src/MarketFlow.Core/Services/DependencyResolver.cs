using MarketFlow.Core.Models;

namespace MarketFlow.Core.Services;

/// <summary>
/// Resolves job execution order via topological sort and detects
/// dependency cycles - the same guarantees an enterprise scheduler
/// (AutoSys / ActiveBatch) provides for batch streams.
/// </summary>
public static class DependencyResolver
{
    /// <summary>
    /// Returns jobs in a valid execution order (dependencies first).
    /// Throws <see cref="InvalidOperationException"/> when a cycle exists
    /// or a dependency references an unknown job.
    /// </summary>
    public static IReadOnlyList<Job> Resolve(IEnumerable<Job> jobs)
    {
        var byName = jobs.ToDictionary(j => j.Name, StringComparer.OrdinalIgnoreCase);
        var sorted = new List<Job>(byName.Count);
        var state = new Dictionary<string, VisitState>(StringComparer.OrdinalIgnoreCase);

        foreach (var name in byName.Keys)
            Visit(name);

        return sorted;

        void Visit(string name)
        {
            if (!byName.TryGetValue(name, out var job))
                throw new InvalidOperationException($"Job '{name}' is referenced as a dependency but is not defined.");

            switch (state.GetValueOrDefault(name))
            {
                case VisitState.Done: return;
                case VisitState.InProgress:
                    throw new InvalidOperationException($"Dependency cycle detected involving job '{name}'.");
            }

            state[name] = VisitState.InProgress;
            foreach (var dep in job.DependsOn)
                Visit(dep);

            state[name] = VisitState.Done;
            sorted.Add(job);
        }
    }

    private enum VisitState { NotVisited, InProgress, Done }
}
