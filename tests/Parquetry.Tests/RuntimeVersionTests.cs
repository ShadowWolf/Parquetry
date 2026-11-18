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
    /// nothing would show that. The test is skipped when the variable is not
    /// set, as on a contributor's machine.
    /// </summary>
    [Fact]
    public void Tests_run_on_the_runtime_the_job_asked_for()
    {
        var expected = Environment.GetEnvironmentVariable(ExpectedMajorVariable);
        Assert.SkipWhen(string.IsNullOrEmpty(expected), $"{ExpectedMajorVariable} is not set.");

        Assert.Equal(expected, Environment.Version.Major.ToString(System.Globalization.CultureInfo.InvariantCulture));
    }
}
