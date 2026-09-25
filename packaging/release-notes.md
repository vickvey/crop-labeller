Offline packages for Windows (64-bit). Neither needs internet on the machine that runs it.

| Download | For | What to do |
|---|---|---|
| **`crop-labeller-<version>-windows-offline.zip`** (recommended) | Anyone | Unblock → Extract All → double-click `start-crop-labeller.bat`. Python is built in, so nothing needs installing. |
| `crop-labeller-<version>-windows-offline-own-python.zip` | Machines that must use their own Python **3.12 (64-bit)** | Unblock → Extract All → double-click `install-with-own-python.bat` once, then `start-crop-labeller.bat`. |

Step-by-step instructions (with troubleshooting) are in `USAGE-GUIDELINES.pdf` inside each zip, section 8.
`SHA256SUMS.txt` lists checksums for checking a copy, e.g. after moving it by USB:
`certutil -hashfile crop-labeller-<version>-windows-offline.zip SHA256`.

Every package in this release was built from the tagged commit and tested on Windows before publishing.
