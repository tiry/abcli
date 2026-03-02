# Spec 35: Automated Source Build Installation Scripts

## Problem Statement

Currently, installing ab-cli from source requires manually executing multiple commands (create venv, install dependencies, run build). This process is error-prone and time-consuming for users who want to:
- Install from source for the first time
- Update their installation by pulling latest changes
- Ensure proper Python version and dependencies

## Goals

1. Create automated installation scripts that handle the complete setup process
2. Provide scripts for both POSIX (Linux/macOS) and Windows platforms
3. Include option to update existing installation (git pull + reinstall)
4. Validate prerequisites (Python version) before proceeding
5. Update documentation to reference the new scripted installation option

## Clarifying Questions

### 1. **Script Location**
- Confirm scripts should be in `ab-cli/scripts/` directory (not `nightly/`)
- Script names: `install.sh` and `install.ps1`?

=> YES / YES

### 2. **Installation Mode**
Should the script support both:
- **Fresh install**: Create venv, install dependencies, build
- **Update mode** (with `--update` flag): Git pull, reinstall dependencies, rebuild

=> YES the script should support both option using --update to trigger update (false by default)

Or should update be a separate script?

### 3. **Installation Type**
Which installation should the script perform:
- Development installation: `pip install -e ".[dev]"` (includes dev dependencies)?
- Or standard: `pip install -e .`?
- Or offer both as an option?

=> use dev installation since this is more likely to be properly tested

### 4. **Python Version Requirement**
- Minimum Python version: 3.10?
- Should script check for specific version or any 3.10+?

=> check that python and available and log a warn is the version is too old

### 5. **Build Step**
Should the script run `python -m build` to create wheel/sdist?
- Or just do `pip install -e .` which doesn't require build step?
- Current INSTALL.md mentions `python -m build` in "Building from Source" section

=> pip install is enough for now

### 6. **Error Handling**
What should happen if:
- Python version is too old?

=> warn but try

- Git is not installed (for update mode)?

=> warn and skip

- venv already exists?

=> prompt user to overwrite or not, not => abort

- Installation fails?

=> display error messsage

Should the script:
- Exit with error message?

=> yes stop on errors

- Offer to continue anyway?
- Clean up and retry?

### 7. **Virtual Environment Location**
- Use `venv/` in the ab-cli root directory (as per current docs)?
- Any other preferences?

=> yes use venv/

### 8. **Post-Install Verification**
Should the script:
- Run `ab --version` to verify installation?
- Run `ab validate` to check config?
- Just complete silently if successful?

=> prompt the user to do this, but let user to do it or not

### 9. **Configuration**
Should the script:
- Check if `config.yaml` exists?
- Offer to create from `config.example.yaml`?
- Or leave configuration as manual step (as currently documented)?

=> yes, just suggest to run the configuration command

### 10. **PATH Activation Guidance**
Should the script:
- Show instructions on how to activate venv for future sessions?
=> yes
- Create an activation alias/script?
=> no
- Just remind user to run `source venv/bin/activate`?
=> yes

## Proposed Implementation

### Files to Create:
1. `ab-cli/scripts/install.sh` - POSIX installation script
2. `ab-cli/scripts/install.ps1` - Windows PowerShell script

### Files to Modify:
1. `ab-cli/doc/INSTALL.md` - Add "Automated Installation" section

### Script Features:
- Check Python 3.10+ is available
- Create virtual environment if needed
- Install package with dependencies
- Verify installation
- Support `--update` flag for git pull + reinstall
- Colorized output for better UX
- Clear error messages

### Usage Examples:
```bash
# POSIX
./scripts/install.sh           # Fresh install
./scripts/install.sh --update  # Update existing installation

# Windows
.\scripts\install.ps1           # Fresh install
.\scripts\install.ps1 -Update   # Update existing installation
```

## Questions for User Review

Please review the clarifying questions above and let me know:
1. Which installation type should be default?
2. Should we include the build step or just pip install?
3. How should we handle existing venv directories?
4. Should scripts handle config file creation or leave manual?
5. Any other preferences or requirements?

Once these are clarified, I'll implement the solution.
