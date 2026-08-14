# Application Migration Analyzer

Ansible-based inventory and complexity analyzer for legacy .NET and Visual
Basic source code, complemented by a Showroom-style learning path for running
Red Hat Migration Toolkit for Applications (MTA) from the command line.

## Documentation

The workshop covers:

- Preparing RHEL 8, RHEL 9, or RHEL 10.
- Installing JDK 17+, Maven 3.9.9+, Podman, and MTA CLI 8.2.
- Running Java source and binary analyses.
- Running containerized C# source analyses.
- Handling Visual Basic honestly with the repository's heuristic analyzer when
  no native MTA semantic provider is available.
- Reviewing, copying, and serving static MTA reports.

After GitHub Pages is enabled with **GitHub Actions** as its source, the
published learning path is available at:

`https://psehgaft.github.io/ansible_app-migration_analyzer/ansible-app-migration-analyzer/main/ARCHITECTURE/index.html`

Build the site locally:

```bash
npm install --global @antora/cli@3.1 @antora/site-generator@3.1
antora generate default-site.yml --stacktrace
```

The generated site is written to `www/`.

## .NET Framework analysis with .NET Upgrade Assistant

> [!IMPORTANT]
> Microsoft has officially deprecated .NET Upgrade Assistant in favor of the
> GitHub Copilot modernization agent. The legacy Upgrade Assistant remains
> useful when Copilot cannot be used, but new long-lived automation should not
> depend on it. Microsoft's current supported prerequisites require a Windows
> operating system; installing the .NET SDK on RHEL does not make Upgrade
> Assistant a supported Linux workflow.

.NET Upgrade Assistant complements MTA by analyzing and upgrading C# or Visual
Basic projects from .NET Framework to modern .NET. It supports project types
such as ASP.NET, Windows Forms, WPF, class libraries, and console applications.
Use it on a dedicated Windows workstation or VM, and keep MTA CLI on the RHEL
analysis server.

### Recommended topology

| Host | Tools | Purpose |
|---|---|---|
| RHEL 8, 9, or 10 | MTA CLI, Podman, Java, Maven | Java and containerized C# migration analysis |
| Windows workstation or VM | Visual Studio, .NET SDK, .NET Upgrade Assistant | Supported .NET Framework C#/VB analysis and upgrade planning |

### Windows prerequisites

Install or provide all of the following:

- A supported Windows operating system.
- Visual Studio 2026, or Visual Studio 2022 version 17.14.17 or later.
- .NET SDK 8 or later. This guide uses the .NET 8 SDK as the minimum baseline.
- Visual Studio workloads required by the application:
  - **.NET desktop development** for Windows Forms, WPF, console apps, and
    class libraries.
  - **ASP.NET and web development** for ASP.NET applications.
- The .NET Framework Developer Pack or Targeting Pack matching every framework
  targeted by the solution, for example .NET Framework 4.7.2 or 4.8.
- Git and authenticated access to the source repository.
- HTTPS access to `api.nuget.org` or the approved enterprise NuGet mirror.
- Access to private package feeds and vendor dependencies required to restore
  and build the solution.

Do not analyze the only working copy. Clone the repository and create a branch
or a complete backup before running any upgrade action.

### Install and validate the .NET SDK

Install the .NET 8 SDK from the official Microsoft installer or your managed
enterprise software catalog. Then open a new PowerShell terminal:

```powershell
dotnet --info
dotnet --list-sdks
dotnet --list-runtimes
```

The output must show .NET SDK 8.0 or later. The SDK includes the matching .NET
runtime; a separate runtime installation is not required for the CLI tool.

### Install .NET Upgrade Assistant

The CLI is distributed as the `upgrade-assistant` .NET global tool:

```powershell
dotnet tool install --global upgrade-assistant
```

If organization-specific NuGet sources are temporarily unavailable, Microsoft
documents the following installation fallback:

```powershell
dotnet tool install --global --ignore-failed-sources upgrade-assistant
```

Use `--ignore-failed-sources` only after confirming that the official or
approved feed remains reachable. Do not use it to conceal a missing trusted
package source.

The global-tool directory is normally added to `PATH` by the SDK. If the
command is not found, add the following user directory and open a new terminal:

```text
%USERPROFILE%\.dotnet\tools
```

Validate the installation:

```powershell
dotnet tool list --global
upgrade-assistant --version
upgrade-assistant --help
```

To update an existing installation:

```powershell
dotnet tool update --global upgrade-assistant
```

For repeatable assessments, record the version returned by
`upgrade-assistant --version`; avoid silently changing the tool version during
an assessment campaign.

### Prepare a .NET Framework solution

```powershell
git clone https://github.com/OWNER/REPOSITORY.git
Set-Location REPOSITORY
git switch -c assessment/net-framework-modernization

dotnet nuget list source
dotnet restore .\Application.sln
```

Older non-SDK-style .NET Framework solutions might require Visual Studio
MSBuild and NuGet instead of `dotnet restore`:

```powershell
nuget restore .\Application.sln
msbuild .\Application.sln /t:Build /p:Configuration=Release
```

Resolve missing targeting packs, private packages, project references, and
vendor DLLs before trusting the analysis. A solution that cannot be loaded or
restored can produce incomplete recommendations.

### Generate an analysis report without upgrading

Run the interactive analyzer from the directory containing the `.sln`,
`.csproj`, or `.vbproj` file:

```powershell
Set-Location C:\src\Application
upgrade-assistant analyze
```

In the interactive wizard:

1. Select **Application sources**.
2. Select the proposed target framework, for example **.NET 8.0**.
3. Select the source, dependency, and configuration components to scan.
4. Select the applicable configuration file or choose no configuration file.
5. Select **Save as HTML**.
6. Enter a report name.
7. Select the privacy mode required by the organization, such as
   **Restricted**.
8. Review the summary and confirm the analysis.

The report is written below the analyzed solution or project directory. Save
the report together with the source commit, Upgrade Assistant version, target
framework, execution date, and analyst name.

### Run an upgrade only after reviewing the report

Upgrade Assistant modifies project and source files. Commit the clean baseline
and create a dedicated branch first:

```powershell
git status --short
git add --all
git commit -m "Record pre-upgrade baseline"
git switch -c modernization/net8

upgrade-assistant upgrade
```

The upgrade command is interactive. Upgrade projects in dependency order:
shared libraries first, then the applications that consume them. Select the
target framework and upgrade type only after reviewing the generated analysis.

After the upgrade:

```powershell
dotnet restore .\Application.sln
dotnet build .\Application.sln --configuration Release
dotnet test .\Application.sln --configuration Release
git status --short
git diff --stat
```

Windows Forms, WPF, COM, registry access, Windows services, IIS, and other
Windows-specific dependencies can remain Windows-specific after the framework
upgrade. A successful conversion to modern .NET does not automatically make an
application Linux- or container-compatible.

### Optional .NET SDK on the RHEL analysis server

The .NET SDK is supported on RHEL 8, 9, and 10 and can be useful for compiling
modern cross-platform projects after conversion. It is not required by MTA's
containerized C# provider and does not make .NET Upgrade Assistant supported on
RHEL.

```bash
sudo dnf install -y \
  glibc libgcc ca-certificates openssl-libs libstdc++ \
  libicu tzdata krb5-libs zlib
sudo dnf install -y dotnet-sdk-8.0

dotnet --info
dotnet --list-sdks
dotnet --list-runtimes
```

### Combined assessment workflow

1. Run MTA on RHEL for Java and C# migration-rule findings.
2. Run .NET Upgrade Assistant `analyze` on Windows for .NET Framework C# and
   Visual Basic compatibility findings.
3. Run this repository's Ansible analyzer for an additional heuristic inventory
   of C#, VB, WCF, Web Forms, WSDL, and Windows API usage.
4. Keep each report's tool name, version, platform, source commit, and evidence
   provenance separate.
5. Consolidate the findings into one modernization backlog and validate the
   proposed target with a proof of concept.

Official references:

- [Install .NET Upgrade Assistant](https://learn.microsoft.com/en-us/dotnet/core/porting/upgrade-assistant-install)
- [Analyze projects with .NET Upgrade Assistant](https://learn.microsoft.com/en-us/dotnet/core/porting/upgrade-assistant-how-to-analyze)
- [Upgrade projects with .NET Upgrade Assistant](https://learn.microsoft.com/en-us/dotnet/core/porting/upgrade-assistant-how-to-upgrade)
- [.NET Upgrade Assistant overview and supported project types](https://learn.microsoft.com/en-us/dotnet/core/porting/upgrade-assistant-overview)
- [Install .NET on RHEL](https://learn.microsoft.com/en-us/dotnet/core/install/linux-rhel)

## Existing Ansible analyzer

```bash
sudo dnf install -y ansible-core python3
ansible-playbook playbook.yml \
  -e "source_code_path=/path/to/legacy-source" \
  -e "output_dir=/path/to/report"
```

The Ansible role provides a heuristic inventory. It is not a replacement for
MTA's Java or C# semantic providers.
