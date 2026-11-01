## 5. Prerequisites and installation evidence

1. Use the intended Windows account. Confirm the selected fixed drive exists and sufficient disk/RAM/VRAM is available. The chat does not establish universal minimum hardware for the model/context.
2. Install Python from the official Windows distribution [R1]. Python 3.12 was observed, but its patch version was not captured. Select PATH integration. Record exact installed version and executable. Do not silently upgrade the language major/minor version without acceptance testing.
3. Install Poppler Windows binaries from the upstream Windows packaging project [R2]. The observed machine used the WinGet package `oschwartz10612.Poppler`; its exact original installation command is not in the transcript. The following discovery/install procedure is reconstructed, not historical proof:

```powershell
winget show --id oschwartz10612.Poppler --exact --source winget
winget install --id oschwartz10612.Poppler --exact --source winget
```

Review the package metadata/version before installing. Reopen PowerShell after PATH changes.

4. Install OneDrive for Business and sign in to the same account used by the flow. Select the client's sync location. In File Explorer mark Incoming “Always keep on this device” to make files locally available [R3]. Record sync health; a locally created result folder is not evidence that the cloud upload has finished.
5. Install LM Studio from its official site [R4], install the client-approved model and start its local server. Record app version, inference runtime/backend, model file and checksum. The exact original LM Studio/Python installers and versions are unavailable, so this is a replication prerequisite, not an invented installation transcript.
6. This code uses Python standard-library modules. Do not add an OCR engine: Poppler extracts selectable PDF text and renders image pages, which the local vision model reads. A web framework, cloud SDK, CUDA toolkit, and vector database are not baseline dependencies.

Run this inventory and retain its output:

```powershell
$PSVersionTable
python --version
Get-Command python, pythonw, pdfinfo, pdftotext, pdftoppm -ErrorAction Stop |
    Select-Object Name, Source
pdfinfo -v
pdftotext -v
pdftoppm -v
$env:OneDriveCommercial
Get-PSDrive -PSProvider FileSystem
```

