# MTA .NET analyzer role

This role creates a clean, repeatable C# input workspace and runs the MTA
`csharp` provider in containerized, source-only mode. It preserves solution,
project, source, configuration, package, library, and WSDL files while excluding
common generated directories such as `bin` and `obj`.

The role does not translate Visual Basic into C#. It records `.vb` and
`.vbproj` files in `analysis-scope.json`, but MTA analyzes only the C# portion.
Use the repository's `net_analyzer` role and .NET Upgrade Assistant for VB-only
applications.

## Usage

```bash
ansible-playbook -i localhost, mta-dotnet-analysis.yml \
  -e "mta_dotnet_source_path=/srv/mta/input/application" \
  -e "mta_dotnet_output_dir=/srv/mta/output/application-mta"
```

Set `mta_dotnet_execute_analysis=false` to generate and inspect only the staged
source and manifest. Set `mta_dotnet_fail_on_vb_only=false` to permit a VB-only
inventory run without invoking MTA.

The expected report is
`<mta_dotnet_output_dir>/report/static-report/index.html`.
