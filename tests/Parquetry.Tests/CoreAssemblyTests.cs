using System.Reflection;
using Xunit;

namespace Parquetry.Tests;

/// <summary>
/// Checks rules that apply to the core assembly as a whole.
/// </summary>
public class CoreAssemblyTests
{
    /// <summary>
    /// The core package has no third-party dependencies and no
    /// Microsoft.Extensions dependencies, so every assembly it references
    /// must be one that ships with the .NET runtime.
    /// </summary>
    /// <remarks>
    /// The compiler leaves out a reference that the code does not use, so
    /// this test catches a dependency only once code calls it. The
    /// RejectPackageDependencies target in Parquetry.csproj catches a
    /// package reference as soon as it is added.
    /// </remarks>
    [Fact]
    public void References_only_assemblies_that_ship_with_the_runtime()
    {
        var core = Assembly.Load("Parquetry");
        var runtimeDirectory = Path.GetDirectoryName(typeof(object).Assembly.Location)!;

        var notInRuntime = core.GetReferencedAssemblies()
            .Select(reference => reference.Name!)
            .Where(name => !File.Exists(Path.Combine(runtimeDirectory, name + ".dll")))
            .ToArray();

        Assert.Empty(notInRuntime);
    }
}
