# DevForge---CyberCriminals


DevForge – Local AI Code Auto-Repair System
Automatic Python Code Debugging & Repair using Local AI (Offline & Secure)

DevForge is an offline, privacy-first debugging system that automatically detects, analyzes, and fixes Python errors. It combines smart rule-based debugging with the power of a local LLM (Ollama – Llama3, Mistral, CodeGemma, etc.), capable of repairing complex multi-line logic errors without needing cloud APIs.

Designed for hackathons, students, developers, and enterprises who need fast debugging without exposing code over the internet.

✨ Key Features

🧠 Automatic code repair, iterative fix loop until success

🛠 Hybrid engine: regex-based fixes + LLM reasoning

🔒 Runs completely offline (no cloud dependencies)

📂 Upload .py file or paste code directly

⚡ Stops early when code is fixed (no wasted iterations)

🧾 Patch logs & iteration history for transparency

💻 Clean web UI built with HTML/CSS/JS + Python backend

🔄 Diff Viewer to compare old vs new code (coming soon)

🪓 Removes dead code, unused imports, invalid blocks when needed

Supports massive multi-line codebases


======================================================================================================================================================


| Step                      | Action                                                            |
| ------------------------- | ----------------------------------------------------------------- |
| 1️⃣ Code Input            | User pastes code or uploads `.py`                                 |
| 2️⃣ Execution             | Code runs in a safe isolated subprocess                           |
| 3️⃣ Error Analysis        | System parses Python traceback & extracts error type/message      |
| 4️⃣ Patch Decision Engine | If common error → auto fix via rule handler                       |
| 5️⃣ AI Repair (fallback)  | If complex error → send code + errors to **local LLM via Ollama** |
| 6️⃣ Patch Apply           | New code is generated and rerun                                   |
| 7️⃣ Iteration Loop        | Continue until success or irreparable failure                     |
| 8️⃣ Output                | Final fixed code displayed with patch history                     |




======================================================================================================================================================



Project Structure
DevForge/
│── index.html         # Frontend UI
│── app.js             # Frontend logic + REST calls
│── server.py          # Flask/FastAPI backend
│── controller.py      # Repair loop controller
│── runner.py          # Safe code execution subprocess
│── analyzer.py        # Error extraction logic
│── patcher.py         # Patch generator + calls LLM
│── llm_handler.py     # Ollama interface
│── models.py          # Dataclasses (logging & results)



======================================================================================================================================================


<h1> With Love ❤️ Proud OSC Member </h1>

