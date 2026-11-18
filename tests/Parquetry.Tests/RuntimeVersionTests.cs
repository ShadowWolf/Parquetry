using System.Globalization;
using Xunit;

namespace Parquetry.Tests;

/// <summary>
/// Confirms which .NET runtime the tests ran on.
/// </summary>
public class RuntimeVersionTests
{
    /// <summary>
    /// The name of the environment variable that holds the major version of
    /// the runtime the tests are meant to run on, such as 11.
    /// </summary>
    private const string ExpectedMajorVariable = "PARQUETRY_EXPECTED_RUNTIME_MAJOR";

    /// <summary>
    /// The library targets .NET 10, and continuous integration also runs
    /// these tests on a later runtime. Each job sets the variable to the
    /// version it means to test, and this test fails if the tests ran on a
    /// different one. Without it, a job could pass on the wrong runtime and
    /// nothing would show that.
    /// </summary>
    /// <remarks>
    /// On GitHub Actions the test fails if the variable is not set, so that
    /// a job cannot lose the check by losing the variable. Anywhere else,
    /// such as on a contributor's machine, the test is skipped when the
    /// variable is not set.
    /// </remarks>
    [Fact]
    public void Tests_run_on_the_runtime_the_job_asked_for()
    {
        var expected = Environment.GetEnvironmentVariable(ExpectedMajorVariable);
        if (string.IsNullOrEmpty(expected))
        {
            // GitHub Actions sets GITHUB_ACTIONS to "true" in every job.
            Assert.False(
                Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true",
                $"{ExpectedMajorVariable} is not set. Every job in the workflow must set it.");
            Assert.Skip($"{ExpectedMajorVariable} is not set.");
        }

        Assert.Equal(expected, Environment.Version.Major.ToString(CultureInfo.InvariantCulture));
    }
}
