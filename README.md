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

## Prepare the RHEL server for MTA CLI

Complete this section before running MTA manually or through the
`mta_dotnet_analyzer` role. The examples target MTA 8.2 on RHEL 8, RHEL 9, or
RHEL 10 and assume that analyses run as an unprivileged service or analysis
user.

### Select the analysis mode

| Application input | MTA provider and mode | Host preparation |
|---|---|---|
| Java source | Java, containerless or container | JDK 17+, Maven 3.9.9+; Podman and registry access when container mode is selected |
| Java binary archives | Java binary analysis | JDK 17+, sufficient temporary storage, original deployment archives |
| C# source | `csharp`, containerized `source-only` mode | Podman, Red Hat registry authentication, `.sln` or `.csproj`, C# source, dependencies, and applicable rules |
| Visual Basic source | No native MTA semantic provider | Use the repository heuristic role and .NET Upgrade Assistant on Windows; do not represent this as an MTA result |

The automated role in this repository uses the C# provider with
`--run-local=false` and `--mode source-only`.

### Host, access, and capacity checklist

Prepare all of the following before installation:

- A supported `x86_64` or `aarch64` RHEL 8, 9, or 10 server.
- A named, unprivileged analysis account with `sudo` access for installation.
- An active Red Hat subscription, Satellite content view, or approved internal
  RHEL repository mirror.
- A Red Hat account authorized to download MTA and authenticate to
  `registry.redhat.io`.
- DNS, NTP, and outbound HTTPS connectivity, or approved internal mirrors.
- Access to the application Git repository or a verified source archive.
- Access to required Maven, NuGet, and vendor dependency repositories.
- Credentials for private artifact feeds stored outside Git and playbook
  variables.
- Enough space for the original source, normalized copy, container images,
  dependency caches, MTA working data, and final reports.

Use this baseline for one analysis at a time:

| Resource | Minimum lab | Recommended analysis server |
|---|---:|---:|
| CPU | 2 vCPU | 4 or more vCPU |
| RAM | 8 GiB | 16 GiB or more |
| Free disk | 30 GiB | 100 GiB or more |
| File system | XFS or ext4 | XFS with a separate `/srv/mta` workspace |

Large monorepositories, retained reports, parallel analyses, or large provider
images require additional CPU, RAM, and storage. Monitor the first
representative application before setting a shared-server concurrency limit.

Inspect the host:

```bash
cat /etc/redhat-release
uname -m
getenforce
timedatectl status
free -h
df -hT
```

The MTA archive suffix is `linux-amd64` for `x86_64` and `linux-arm64` for
`aarch64`.

### Register RHEL and validate repositories

Skip registration only when Satellite or another approved content-management
system already manages the host.

```bash
sudo subscription-manager status
sudo subscription-manager register
sudo subscription-manager refresh
sudo subscription-manager repos --list-enabled
sudo dnf -y makecache
```

Never place Red Hat passwords, registry tokens, proxy credentials, Maven
passwords, or NuGet API keys in shell scripts, Git, command-line extra
variables, or unencrypted Ansible variable files.

### Install operating-system packages

Install the common CLI, archive, security, and Ansible dependencies:

```bash
sudo dnf -y install \
  ansible-core ca-certificates curl findutils git gzip jq openssl \
  procps-ng python3 shadow-utils tar unzip which
```

Install Podman and its supporting container tools.

RHEL 8:

```bash
sudo dnf -y module reset container-tools
sudo dnf -y module install container-tools:rhel8
```

RHEL 9 or RHEL 10:

```bash
sudo dnf -y install container-tools
```

If Satellite exposes `container-tools` as ordinary packages instead of a RHEL
8 module stream, follow the approved content-view procedure.

### Create the analysis account and directory layout

The following example assumes that `mta-analysis` is a dedicated local
account. Integrate it with the organization's identity and privilege policy
when centralized identity management is used.

```bash
id mta-analysis >/dev/null 2>&1 || \
  sudo useradd --create-home --shell /bin/bash mta-analysis
sudo install -d -m 0755 /opt/mta
sudo install -d -m 0750 -o mta-analysis -g mta-analysis \
  /srv/mta/input /srv/mta/output /srv/mta/rules /srv/mta/cache
```

Do not make the workspace world-writable. Application source, configuration,
WSDL contracts, dependency metadata, and reports can contain sensitive
information. Keep source read-only where practical, and create a separate
output directory for each assessment or use `--overwrite` only intentionally.

Validate access as the analysis user:

```bash
sudo -iu mta-analysis
test -r /srv/mta/input
test -w /srv/mta/output
test -w /srv/mta/cache
umask 027
```

### Configure rootless Podman

C# and other non-Java providers run in container mode. Verify subordinate UID
and GID allocations and container storage for the analysis account:

```bash
id
grep "^$(id -un):" /etc/subuid /etc/subgid
podman --version
podman info --debug
```

If subordinate ranges are absent, an administrator must allocate them under
the organization's identity policy. After changing ranges, run the following
as the analysis user:

```bash
podman system migrate
```

Test image pulls and rootless execution:

```bash
podman run --rm registry.access.redhat.com/ubi9/ubi-minimal true
podman login registry.redhat.io
podman login --get-login registry.redhat.io
```

Use interactive login or the enterprise secret manager. Do not put registry
credentials on the command line or in this repository. Confirm that container
storage has sufficient space:

```bash
podman info --format json | jq '.store'
df -h "$HOME/.local/share/containers" /var/lib/containers 2>/dev/null || true
```

### Configure proxy, DNS, firewall, and certificate trust

Allow or mirror the endpoints required by the selected workflow:

- `registry.redhat.io` for MTA provider images.
- `registry.access.redhat.com` for Red Hat base-image validation.
- `developers.redhat.com` for the authorized MTA CLI download.
- The organization's source-control endpoints.
- Approved Maven repositories or mirrors for Java dependencies.
- Approved NuGet feeds or mirrors for C# dependencies.
- Any private vendor artifact repositories referenced by the application.

When an outbound proxy is required, configure it in the analysis account's
managed environment rather than embedding credentials in the repository:

```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
export NO_PROXY="localhost,127.0.0.1,.example.com"

curl -I https://registry.redhat.io/v2/
curl -I https://developers.redhat.com/
```

Install the enterprise CA chain instead of disabling TLS verification:

```bash
sudo install -m 0644 organization-root-ca.pem \
  /etc/pki/ca-trust/source/anchors/organization-root-ca.pem
sudo update-ca-trust
openssl s_client -connect registry.redhat.io:443 \
  -servername registry.redhat.io </dev/null
```

Provider containers must also trust internal Maven, NuGet, proxy, and source
control certificates. Validate that requirement with a representative provider
run; host trust alone does not prove that an internal endpoint is trusted
inside every container image.

### Install JDK 17 or later

MTA 8.2 requires JDK 17 or later for the supported CLI preparation flow.

```bash
sudo dnf -y install java-17-openjdk-devel

JAVA_BIN="$(readlink -f "$(command -v java)")"
MTA_JAVA_HOME="${JAVA_BIN%/bin/java}"
printf 'Detected JAVA_HOME: %s\n' "$MTA_JAVA_HOME"
java -version
javac -version
```

Persist `JAVA_HOME` for the analysis environment:

```bash
sudo tee /etc/profile.d/mta-java.sh >/dev/null <<EOF
export JAVA_HOME="$MTA_JAVA_HOME"
export PATH="\$JAVA_HOME/bin:\$PATH"
EOF
sudo chmod 0644 /etc/profile.d/mta-java.sh
source /etc/profile.d/mta-java.sh
```

If the approved RHEL 10 content view provides a later supported OpenJDK instead
of OpenJDK 17, install that JDK and derive `JAVA_HOME` with the same procedure.

### Install Maven 3.9.9 or later

First inspect the version supplied by the enabled RHEL repositories:

```bash
dnf info maven | sed -n '/^Version/p'
```

Install it with DNF only if the offered version is 3.9.9 or later. Otherwise,
download an Apache Maven binary and its checksum on a trusted workstation,
copy both files to the server, and verify them before installation. This
example uses Maven 3.9.11:

```bash
MTA_MAVEN_VERSION=3.9.11
MTA_MAVEN_ARCHIVE="apache-maven-${MTA_MAVEN_VERSION}-bin.tar.gz"

sha512sum -c "${MTA_MAVEN_ARCHIVE}.sha512"
sudo tar -xzf "$MTA_MAVEN_ARCHIVE" -C /opt
sudo ln -sfn "/opt/apache-maven-${MTA_MAVEN_VERSION}" /opt/maven

sudo tee /etc/profile.d/mta-maven.sh >/dev/null <<'EOF'
export MAVEN_HOME=/opt/maven
export PATH="$MAVEN_HOME/bin:$PATH"
EOF
sudo chmod 0644 /etc/profile.d/mta-maven.sh
source /etc/profile.d/mta-maven.sh
mvn --version
```

For private Java dependencies, install the approved mirror configuration as
`~/.m2/settings.xml`, protect it with mode `0600`, and confirm that Maven can
resolve the application's dependencies. Do not commit the settings file when
it contains credentials.

### Download and install MTA CLI 8.2

Download the archive matching `uname -m` from the official Red Hat MTA download
page using an authorized account:

- `mta-8.2.0-cli-linux-amd64.zip` for `x86_64`.
- `mta-8.2.0-cli-linux-arm64.zip` for `aarch64`.

Copy the archive to the analysis server, record its checksum in the assessment
evidence, and install it for the analysis user:

```bash
MTA_VERSION=8.2.0
case "$(uname -m)" in
  x86_64) MTA_ARCH=linux-amd64 ;;
  aarch64) MTA_ARCH=linux-arm64 ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

MTA_ZIP="mta-${MTA_VERSION}-cli-${MTA_ARCH}.zip"
test -s "$MTA_ZIP"
sha256sum "$MTA_ZIP" | tee "${MTA_ZIP}.sha256"
install -d -m 0755 "$HOME/.kantra" "$HOME/.local/bin"
unzip -q "$MTA_ZIP" -d "$HOME/.kantra"

MTA_BIN="$(find "$HOME/.kantra" -maxdepth 3 -type f \
  -name mta-cli -print -quit)"
test -n "$MTA_BIN"
chmod 0755 "$MTA_BIN"
ln -sfn "$MTA_BIN" "$HOME/.local/bin/mta-cli"
export PATH="$HOME/.local/bin:$PATH"
```

Persist `$HOME/.local/bin` in the analysis account's managed shell profile.
Do not separate the binary from required directories extracted from the MTA
archive.

Validate the CLI:

```bash
mta-cli version
mta-cli --help
mta-cli provider list
mta-cli rules list-sources
mta-cli rules list-targets
```

The provider list must include `csharp` before running this repository's MTA
.NET role. Use source and target names returned by the installed CLI rather
than assuming that labels remain unchanged between releases.

### Prepare Java application inputs

For a Java source analysis, provide the complete buildable project, including
the root `pom.xml` or Gradle files, modules, source, resources, configuration,
wrappers, and any checked-in organization-approved dependencies. Before MTA:

```bash
cd /srv/mta/input/java-application
git status --short
mvn -q -DskipTests package
```

For binary analysis, preserve the original EAR, WAR, JAR, or deployment archive
and record its checksum. Do not replace a production artifact with a locally
rebuilt file without recording that difference.

Resolve missing repositories, parent POMs, plugins, certificates, proxy
settings, and private dependencies before relying on MTA dependency findings.

### Prepare C#/.NET application inputs

Provide a complete source checkout containing:

- At least one `.sln` or `.csproj` and the referenced C# source files.
- All project-to-project references and shared project directories.
- `Directory.Build.props`, `Directory.Build.targets`, `global.json`,
  `packages.config`, and application configuration files when present.
- A sanitized `NuGet.Config` that identifies approved sources without exposing
  credentials.
- Checked-in `packages/`, `lib/`, DLL, generated-client, schema, and WSDL files
  required by older .NET Framework projects.
- Git submodules or external source components required by the solution.
- A source commit SHA, branch or tag, acquisition date, and application owner.

Inventory the input before execution:

```bash
MTA_DOTNET_INPUT=/srv/mta/input/legacy-application
test -d "$MTA_DOTNET_INPUT"
find "$MTA_DOTNET_INPUT" -type f \
  \( -name '*.sln' -o -name '*.csproj' -o -name '*.vbproj' \
     -o -name 'NuGet.Config' -o -name 'packages.config' \
     -o -name 'Directory.Build.*' \) -print
```

Remove or exclude stale `bin`, `obj`, `.vs`, test-result, package-cache, and
previous-report directories from the analysis copy. Do not delete them from
the original working repository. The role performs this exclusion in its
managed normalized copy.

For mixed C# and Visual Basic solutions, preserve the complete solution to
retain references, but record that MTA findings cover only the C# portion.
Run the repository heuristic analyzer and the Windows Upgrade Assistant flow
for Visual Basic evidence.

### Prepare private dependency access

Before the scheduled analysis window, test every dependency source with the
same account, proxy, DNS, and CA configuration used by MTA:

```bash
mvn -q help:effective-settings >/dev/null
curl -fsSI https://approved-nuget.example.com/v3/index.json >/dev/null
```

Use the organization's secret manager, short-lived tokens, or protected
environment-specific files. Never copy credentials into application source,
`analysis-scope.json`, custom rules, the HTML report, or PR content. Confirm
that report-retention and log-sharing procedures do not expose dependency URLs
or credentials.

### Select and validate rules

An MTA provider produces findings only when applicable rules run. Decide and
record:

- The migration source and target technologies.
- Whether default rulesets are enabled.
- Which custom rules and versions are included.
- The rule owner, approval date, and validation evidence.
- Known exclusions and accepted limitations.

Validate this repository's bundled C# rules before analysis:

```bash
mta-cli rules test \
  roles/mta_dotnet_analyzer/files/rules/csharp-modernization
```

The bundled rules are starter triage rules, not complete coverage for every
framework, vendor library, security control, or target architecture.

### Prepare disconnected environments

For a disconnected container-mode installation:

1. Install the same MTA CLI version on a connected staging host.
2. Authenticate the staging host to `registry.redhat.io`.
3. Run a representative analysis for every required provider so MTA pulls only
   the necessary images.
4. Record `podman images`, image digests, and MTA version.
5. Export images with `podman save`, transfer them through the approved media
   process, and import them with `podman load`.
6. Mirror Maven, NuGet, Git, base images, and custom rules required by the
   applications.
7. Configure enterprise CA trust and repeat the readiness test offline.

Dependency analysis can produce fewer or less accurate incidents when Maven or
NuGet dependencies are unavailable. Record this limitation in every affected
report rather than treating the disconnected result as complete.

### Run the final readiness checks

Run these commands as the same unprivileged account that will execute the
playbook:

```bash
set -o pipefail

cat /etc/redhat-release
uname -m
python3 --version
ansible-playbook --version
java -version
javac -version
test -n "$JAVA_HOME"
mvn --version
podman --version
podman info --format json >/dev/null
podman login --get-login registry.redhat.io
mta-cli version
mta-cli provider list | tee /tmp/mta-providers.txt
grep -qi csharp /tmp/mta-providers.txt
test -r /srv/mta/input
test -w /srv/mta/output
test -w /srv/mta/cache
df -h /srv/mta "$HOME/.local/share/containers" 2>/dev/null || true
```

Do not start the application analysis until all applicable checks pass. Also
record the MTA version, ruleset version, provider list, source commit, input
checksum or inventory, execution date, analyst, and output location for each
assessment.

Official MTA references:

- [Installing MTA 8.2 CLI](https://docs.redhat.com/en/documentation/migration_toolkit_for_applications/8.2/html/installing_the_migration_toolkit_for_applications/installing-mta-cli_installing-mta-title)
- [Using MTA 8.2 CLI](https://docs.redhat.com/en/documentation/migration_toolkit_for_applications/8.2/html/using_the_migration_toolkit_for_applications_command-line_interface)
- [Configuring and using MTA rules](https://docs.redhat.com/en/documentation/migration_toolkit_for_applications/8.2/html/configuring_and_using_rules_for_an_mta_analysis)

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

### Final preflight for this role

Complete the server-preparation procedure above, then verify:

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
