# CONVENTIONS (binding on operator, assistant, and Super Agent)
1. Every code block MUST be prefixed with its interpreter:
   POWERSHELL | PYTHON FILE BODY | CMD | MANUAL(UI)
2. Python is NEVER pasted at a PS> prompt. Python = .py file in 90-scripts\ or
   60-tools\python\, invoked as:
   & C:\kite-agent\.venv\Scripts\python.exe <path>
3. Large CSV work = pandas. PowerShell Import-Csv is banned for the Dhan/Kite masters.
4. No symbol, date, count, or rate may appear in any doc unless it was printed by a
   script on this machine, or cited to a URL. Otherwise write [UNVERIFIED].
5. Fail-closed. No "95%", no "<5%", no "operator judgment" pass thresholds.
6. Every script writes an evidence file to 70-ops\status\.
