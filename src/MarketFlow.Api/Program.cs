using System.Text.Json;
using System.Text.Json.Serialization;
using MarketFlow.Core.Models;
using MarketFlow.Core.Services;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.Converters.Add(new JsonStringEnumConverter()));
builder.Services.AddSingleton(new RetryPolicy());
builder.Services.AddSingleton<JobScheduler>();

var app = builder.Build();
app.UseSwagger();
app.UseSwaggerUI();

// Seed jobs from pipeline definitions produced by tools/jil2pipeline.py
var pipelineDir = Path.Combine(AppContext.BaseDirectory, "pipelines");
if (Directory.Exists(pipelineDir))
{
    var scheduler = app.Services.GetRequiredService<JobScheduler>();
    var options = new JsonSerializerOptions
    {
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter() }
    };
    foreach (var file in Directory.EnumerateFiles(pipelineDir, "*.json"))
        foreach (var job in JsonSerializer.Deserialize<List<Job>>(File.ReadAllText(file), options) ?? [])
            scheduler.Register(job);
}

app.MapGet("/api/health", () => Results.Ok(new { status = "healthy", utc = DateTimeOffset.UtcNow }))
   .WithName("Health");

app.MapGet("/api/jobs", (JobScheduler s) => Results.Ok(s.Jobs))
   .WithName("ListJobs");

app.MapGet("/api/jobs/{name}", (string name, JobScheduler s) =>
        s.Find(name) is { } job ? Results.Ok(job) : Results.NotFound())
   .WithName("GetJob");

app.MapPost("/api/jobs", (Job job, JobScheduler s) =>
        s.Register(job)
            ? Results.Created($"/api/jobs/{job.Name}", job)
            : Results.Conflict(new { message = $"Job '{job.Name}' already exists." }))
   .WithName("RegisterJob");

app.MapPost("/api/pipeline/run", async (JobScheduler s) =>
{
    // Demo executor: replace with Azure Batch / Databricks Jobs API integration.
    var runs = await s.RunAllAsync(async (job, ct) => await Task.Delay(50, ct));
    return Results.Ok(runs.Select(r => new { r.RunId, r.JobName, Status = r.Status.ToString(), r.Attempt }));
}).WithName("RunPipeline");

app.MapGet("/api/runs", (JobScheduler s) =>
        Results.Ok(s.History.OrderByDescending(r => r.StartedAt)))
   .WithName("RunHistory");

app.Run();
