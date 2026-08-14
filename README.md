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

## Existing Ansible analyzer

```bash
sudo dnf install -y ansible-core python3
ansible-playbook playbook.yml \
  -e "source_code_path=/path/to/legacy-source" \
  -e "output_dir=/path/to/report"
```

The Ansible role provides a heuristic inventory. It is not a replacement for
MTA's Java or C# semantic providers.
