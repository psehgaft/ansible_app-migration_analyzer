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

## Automated MTA C# workspace and report

The `mta_dotnet_analyzer` role automates the repeatable preparation and MTA
analysis of a .NET source tree. It copies the application into a managed
workspace, preserves its directory structure, inventories the analysis scope,
installs a starter C# modernization ruleset, invokes the MTA `csharp` provider,
and verifies the generated static HTML report.

This preparation is a source normalization step, not a language conversion.
The role never changes `.cs`, `.vb`, `.sln`, `.csproj`, or `.vbproj` content and
does not translate Visual Basic to C#. MTA receives the staged C# solution or
project in the structure expected by its C# provider.

### Role layout

| Path | Purpose |
|---|---|
| `mta-dotnet-analysis.yml` | Dedicated localhost playbook for the MTA C# workflow |
| `roles/mta_dotnet_analyzer/defaults/main.yml` | Workspace, provider, report, rules, and exclusion defaults |
| `roles/mta_dotnet_analyzer/tasks/main.yml` | Source preparation, preflight validation, MTA execution, and report verification |
| `roles/mta_dotnet_analyzer/files/prepare_mta_dotnet.py` | Safe staging and source-inventory helper |
| `roles/mta_dotnet_analyzer/files/rules/csharp-modernization/` | Starter custom C# ruleset used by the role |

### What the preparation step does

1. Validates that the source is an existing directory.
2. Refuses to place the managed workspace inside the source tree or overwrite
   an unmarked directory.
3. Copies the complete source layout while excluding `.git`, `.vs`, `bin`,
   `obj`, test results, and other generated directories.
4. Preserves solution, project, source, configuration, package, library, DLL,
   and WSDL files needed to understand project references and dependencies.
5. Writes `analysis-scope.json` with the detected `.sln`, `.csproj`, `.vbproj`,
   `.cs`, `.vb`, `.config`, `.dll`, and `.wsdl` files.
6. Requires C# source plus a `.sln` or `.csproj` before invoking MTA.
7. Checks the MTA version, confirms the `csharp` provider, validates Podman and
   the custom ruleset, and runs a containerized source-only analysis.
8. Fails if MTA does not create `report/static-report/index.html`.

The managed workspace marker allows a later run to refresh only the staged
source directory. The role will not recursively replace an arbitrary existing
directory.

### Prerequisites

Complete the RHEL and MTA CLI installation documented by this repository, then
verify:

```bash
ansible-playbook --version
python3 --version
podman info
mta-cli version
mta-cli provider list
```

The provider list must contain `csharp`. Non-Java MTA providers run in
container mode, so the analysis user must have a working rootless Podman
configuration and access to any required provider images and approved NuGet
sources.

### Run the role

```bash
cd /opt/app-migration-analyzer/repository

ansible-playbook -i localhost, mta-dotnet-analysis.yml \
  -e "mta_dotnet_source_path=/srv/mta/input/legacy-application" \
  -e "mta_dotnet_output_dir=/srv/mta/output/legacy-application-mta"
```

Use absolute paths. The output directory must be outside the application
source tree. For repeatable automation, put the variables in an external file:

```yaml
---
mta_dotnet_source_path: "/srv/mta/input/legacy-application"
mta_dotnet_output_dir: "/srv/mta/output/legacy-application-mta"
mta_dotnet_execute_analysis: true
mta_dotnet_validate_rules: true
mta_dotnet_overwrite_report: true
mta_dotnet_enable_default_rulesets: false
mta_dotnet_extra_args: []
```

```bash
ansible-playbook -i localhost, mta-dotnet-analysis.yml \
  -e @/secure/path/mta-dotnet-vars.yml
```

### Generated structure

```text
/srv/mta/output/legacy-application-mta/
├── workspace/
│   ├── .mta-dotnet-workspace
│   ├── analysis-scope.json
│   ├── rules/
│   │   └── csharp-modernization/
│   └── source/
│       ├── Application.sln
│       └── ...
└── report/
    └── static-report/
        └── index.html
```

Open the report from the analysis server with the same loopback HTTP server and
SSH tunnel described below, using:

```bash
cd /srv/mta/output/legacy-application-mta/report/static-report
python3 -m http.server 8080 --bind 127.0.0.1
```

### Variable reference

| Variable | Default | Description |
|---|---|---|
| `mta_dotnet_source_path` | `./legacy_project` in the playbook | Source tree copied into the managed workspace |
| `mta_dotnet_output_dir` | `./migration_report/mta-dotnet` in the playbook | Workspace and report root |
| `mta_dotnet_execute_analysis` | `true` | Run MTA after staging; set to `false` for inventory-only preparation |
| `mta_dotnet_validate_rules` | `true` | Run `mta-cli rules test` before analysis |
| `mta_dotnet_overwrite_report` | `true` | Pass `--overwrite` for a repeatable output location |
| `mta_dotnet_enable_default_rulesets` | `false` | Keep the run scoped to the bundled starter C# rules by default |
| `mta_dotnet_fail_on_vb_only` | `true` | Stop with guidance when no analyzable C# project is present |
| `mta_dotnet_excluded_directories` | Generated and VCS directories | Directory names omitted from the staged copy |
| `mta_dotnet_extra_args` | `[]` | Additional MTA CLI arguments appended as an argv list |

Set both `mta_dotnet_execute_analysis=false` and
`mta_dotnet_fail_on_vb_only=false` to inventory a VB-only tree without calling
MTA. Then run `playbook.yml` for the repository's VB-aware heuristic report and
use .NET Upgrade Assistant on Windows for the supported project-level analysis.

The bundled rules identify selected legacy ASP.NET, WCF, Windows Forms,
Windows Registry, and WebMatrix dependencies. They are a transparent starter
ruleset, not a complete modernization assessment. Add tested,
organization-approved C# rules when the target architecture requires broader
coverage.

## Repository Ansible analysis tool

The repository includes a local Ansible playbook that performs a fast,
read-only heuristic assessment of legacy C# and Visual Basic source trees. It
counts source artifacts, detects selected migration blockers, copies discovered
WSDL contracts, calculates indicative complexity levels for two target paths,
and generates an HTML report.

Use this tool for early discovery and portfolio triage. It complements MTA and
.NET Upgrade Assistant; it does not compile the application or perform
language-semantic analysis.

### Repository layout

| Path | Purpose |
|---|---|
| `playbook.yml` | Local playbook entry point and default input/output paths |
| `roles/net_analyzer/defaults/main.yml` | Role variables and derived report paths |
| `roles/net_analyzer/tasks/main.yml` | Validation, analysis, WSDL collection, report generation, and console summary |
| `roles/net_analyzer/files/analyze_code.py` | Recursive C#/VB source scanner and complexity scoring engine |
| `roles/net_analyzer/templates/report.html.j2` | Jinja2 template for the final HTML report |

### Execution flow

The playbook performs the following ordered operations:

1. Verifies that `source_code_path` exists.
2. Creates the output and WSDL directories.
3. Executes `analyze_code.py` against the source tree.
4. Parses the JSON returned by the Python analyzer into an Ansible fact.
5. Copies discovered `.wsdl` files into the evidence directory.
6. Renders the HTML migration-complexity report.
7. Prints the class count, WSDL count, target complexity, and report location.

The playbook runs against `localhost` with `connection: local`. The application
source must therefore be available on the same machine that runs
`ansible-playbook`, either on a local disk or a mounted file system.

### What the analyzer inspects

The Python scanner recursively examines `.cs`, `.vb`, `.aspx`, and `.wsdl`
files.

| Metric or finding | Detection method | Migration relevance |
|---|---|---|
| C# files | `.cs` extension | Defines the C# assessment scope |
| Visual Basic files | `.vb` extension | Defines the VB/VB.NET assessment scope |
| Classes | Regular expressions for C# and VB class declarations | Provides an approximate structural size |
| Lines of code | Physical lines in `.cs` and `.vb` files | Provides a basic sizing indicator |
| WSDL contracts | `.wsdl` extension | Identifies SOAP service contracts for review |
| ASP.NET Web Forms | `.aspx` extension | Indicates a likely UI rewrite requirement |
| Legacy ASP.NET | `System.Web` found in a source file | Identifies APIs unavailable in modern cross-platform .NET |
| WCF/SOAP | `System.ServiceModel` found in a source file | Identifies service-contract and hosting migration work |
| Native Windows dependencies | `DllImport` or `Microsoft.Win32` found in a source file | Identifies Windows and container portability blockers |
| Legacy data access | `DataSet` or `DataTable` found in a source file | Identifies code that may require data-access redesign |

Pattern metrics count affected source files, not every API invocation inside a
file. The class and line counts are approximations and should not be used as
contractual effort estimates.

### Complexity scoring

The analyzer calculates two independent indicative scores:

| Condition | .NET Core / modern .NET | Java / Quarkus |
|---|---:|---:|
| No escalator detected | Low | Medium |
| At least one WCF file, or more than five files using `System.Web` | Medium | High |
| At least one `.aspx` file or one file using native Windows APIs | High | Very High — rewrite required |

The last matching condition has precedence. For example, a source tree with
both WCF and Web Forms is rated **High** for modern .NET and **Very High
(Rewrite Required)** for Quarkus.

These levels are triage signals. Validate them with MTA, .NET Upgrade
Assistant, dependency analysis, application-owner interviews, and a technical
proof of concept before committing cost or delivery dates.

### Prerequisites

On RHEL 8, 9, or 10:

```bash
sudo dnf install -y ansible-core python3 git

ansible-playbook --version
python3 --version
git --version
```

The current tool uses only Python standard-library modules. No additional
Python packages or Ansible collections are required.

Recommended host resources for a single analysis are 2 vCPU, 4 GiB RAM, and
enough free disk to store the source tree, copied WSDL files, and report. Large
repositories or concurrent runs require additional memory and I/O capacity.

### Clone and validate the repository

```bash
sudo install -d -m 0755 /opt/app-migration-analyzer
sudo chown "$USER":"$(id -gn)" /opt/app-migration-analyzer

git clone \
  https://github.com/psehgaft/ansible_app-migration_analyzer.git \
  /opt/app-migration-analyzer/repository
cd /opt/app-migration-analyzer/repository

ansible-playbook --syntax-check playbook.yml
python3 -m py_compile roles/net_analyzer/files/analyze_code.py
```

### Run with command-line variables

```bash
cd /opt/app-migration-analyzer/repository

ansible-playbook -i localhost, playbook.yml \
  -e "source_code_path=/srv/mta/input/legacy-application" \
  -e "output_dir=/srv/mta/output/legacy-application-heuristic"
```

Use absolute paths for repeatable execution. Quote paths that contain spaces.
The output path can be outside the repository and should not point into the
source tree being analyzed.

### Run with a variables file

Create `analysis-vars.yml` outside the Git repository:

```yaml
---
source_code_path: "/srv/mta/input/legacy-application"
output_dir: "/srv/mta/output/legacy-application-heuristic"
wsdl_output_dir: "/srv/mta/output/legacy-application-heuristic/wsdls"
report_file: "/srv/mta/output/legacy-application-heuristic/migration_report.html"
```

Run the playbook:

```bash
ansible-playbook -i localhost, playbook.yml \
  -e @/secure/path/analysis-vars.yml
```

The variables file must not contain application, registry, or repository
credentials. Protect environment-specific files according to organizational
policy and do not commit them.

### Variable reference

| Variable | Default | Description |
|---|---|---|
| `source_code_path` | `./legacy_project` in `playbook.yml` | Local source directory scanned recursively |
| `output_dir` | `./migration_report` in `playbook.yml` | Root directory for generated evidence |
| `wsdl_output_dir` | `{{ output_dir }}/wsdls` | Directory containing copied WSDL contracts |
| `report_file` | `{{ output_dir }}/migration_report.html` | Final HTML report path |

Variables declared in `playbook.yml` override the role defaults. Command-line
extra variables or an `-e @file.yml` variables file override both.

### Expected output

For `output_dir=/srv/mta/output/legacy-application-heuristic`, the result is:

```text
/srv/mta/output/legacy-application-heuristic/
├── migration_report.html
└── wsdls/
    ├── CustomerService.wsdl
    └── OrderService.wsdl
```

The console summary resembles:

```text
=== ANALYSIS COMPLETE ===
Total classes: 247
WSDL files copied: 2
.NET Core complexity: High
Java (Quarkus) complexity: Very High (Rewrite Required)
Report generated at: /srv/mta/output/legacy-application-heuristic/migration_report.html
```

Open the report locally:

```bash
xdg-open /srv/mta/output/legacy-application-heuristic/migration_report.html
```

For a headless server, serve it only on loopback and use an SSH tunnel:

```bash
cd /srv/mta/output/legacy-application-heuristic
python3 -m http.server 8080 --bind 127.0.0.1
```

```bash
ssh -L 8080:127.0.0.1:8080 analysis-user@mta-server.example.com
```

Open `http://127.0.0.1:8080/migration_report.html` from the workstation.

### Interpreting the report

Review the report in this order:

1. Confirm the analyzed path and source scope.
2. Compare C# and VB file counts with the repository inventory.
3. Validate class and LOC totals as approximate sizing indicators.
4. Review WCF, `System.Web`, Web Forms, and Windows API findings.
5. Inspect every copied WSDL for service ownership and external consumers.
6. Use the target scores to prioritize deeper MTA and Upgrade Assistant work.
7. Record false positives, excluded paths, unreadable files, and manual
   findings in the final assessment.

The HTML template loads Bootstrap styling from a public CDN. In a disconnected
environment, the report content remains available but styling can be limited
unless the dependency is mirrored or embedded under the organization's web
content policy.

### Operational and security considerations

- Run the playbook as an unprivileged analysis user.
- Prefer a read-only source checkout or snapshot.
- Store output outside the application source directory.
- Treat WSDL files as sensitive because they can expose internal endpoints,
  namespaces, operations, and data contracts.
- Restrict report-directory permissions and evidence retention.
- Do not publish customer reports through GitHub Pages.
- Record the repository commit used to run each assessment:

  ```bash
  git rev-parse HEAD
  ```

- Create a new output directory per execution to preserve audit history.
- Check free disk space before scanning large portfolios.

### Current limitations

- The scanner is regex- and text-based; it does not compile source code.
- It does not resolve NuGet dependencies, project references, inheritance,
  reflection, runtime configuration, or generated code semantics.
- Source files that cannot be read are skipped by the Python scanner.
- Findings for `System.Web`, WCF, and native Windows APIs count affected files,
  not individual call sites.
- The current HTML template does not display the internal `DataSet` and
  `DataTable` metric.
- WSDL files with the same basename are copied to the same destination and can
  overwrite one another; review the source inventory when duplicate names
  exist.
- The playbook does not exclude `bin`, `obj`, vendored, generated, test, or
  archive directories automatically.
- The playbook does not persist the raw analyzer JSON as a separate evidence
  file.
- The scores are heuristic and are not equivalent to MTA story points or a
  delivery estimate.

### Troubleshooting

Validate the source path:

```bash
test -d /srv/mta/input/legacy-application
find /srv/mta/input/legacy-application -type f \
  \( -name '*.cs' -o -name '*.vb' -o -name '*.aspx' -o -name '*.wsdl' \) \
  | head -50
```

Check output permissions:

```bash
install -d -m 0750 /srv/mta/output/legacy-application-heuristic
test -w /srv/mta/output/legacy-application-heuristic
```

Run with additional Ansible detail:

```bash
ansible-playbook -i localhost, playbook.yml \
  -e "source_code_path=/srv/mta/input/legacy-application" \
  -e "output_dir=/srv/mta/output/legacy-application-heuristic" \
  -vv
```

Run the Python analyzer directly to isolate playbook or template problems:

```bash
python3 roles/net_analyzer/files/analyze_code.py \
  /srv/mta/input/legacy-application | python3 -m json.tool
```

If the HTML report is not generated, inspect the Ansible failure, confirm that
the analyzer returned valid JSON, and verify that the output directory is
writable. Do not bypass a failed source-path validation.
