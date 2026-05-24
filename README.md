# NotebookLM Mini

A miniature research assistant inspired by Google NotebookLM. You give it a topic, it searches the web, presents the sources it found, you approve the ones you want, and the graph continues with your selection. Built with LangGraph, Tavily, Groq (Llama 3.3 70B), and a Streamlit UI.

## Purpose

This project helps you do fast, human-reviewed topic research.

- It finds web sources for a topic using an agent with search tools.
- It pauses for Human-in-the-Loop approval before continuing.
- It returns curated sources you can trust more than fully automatic output.

---

## How it works

```
User enters topic
       │
       ▼
 [research node]  — ReAct agent runs 2-3 Tavily searches, groups sources by theme
       │
       ▼
[human_review node] — graph pauses with interrupt(); sources are shown in the UI
       │
  User approves
       │
       ▼
 Graph resumes with Command(resume=approved_sources)
       │
       ▼
      END
```

The Human-in-the-Loop pause is implemented with LangGraph's `interrupt()` / `Command(resume=...)` pattern. Graph state is persisted between the pause and resume via an in-memory `MemorySaver` checkpointer.

---

## Project structure

```
.
├── app.py                 # Streamlit UI — all phases (idle, researching, reviewing, done)
├── requirements.txt       # pip-installable dependencies
├── pyproject.toml         # project metadata & build config
└── src/
    ├── agent.py           # ReAct agent built with ChatGroq + Tavily tool
    ├── graph.py           # LangGraph StateGraph (research → human_review)
    ├── human_loop.py      # Source parser (4 regex strategies) + Rich CLI helpers
    ├── main.py            # CLI entry-point (non-Streamlit usage)
    ├── state.py           # ResearchState TypedDict
    ├── summariser.py      # Placeholder for future summarisation step
    └── tools.py           # TavilySearch tool factory
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| [Groq API key](https://console.groq.com/) | Free tier — Llama 3.3 70B (12k TPM) |
| [Tavily API key](https://app.tavily.com/) | Free tier — 1 000 searches/month |

---

## Setup

1. **Clone the repo and create a virtual environment**

   ```bash
   git clone https://github.com/le7-3609/langchain-notebooklm
   cd langchain-notebooklm
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   Or with [uv](https://github.com/astral-sh/uv):

   ```bash
   uv pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root:

   ```env
   GROQ_API_KEY=your_groq_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```

4. **Run the Streamlit app**

   ```bash
   streamlit run app.py
   ```

   The app opens at `http://localhost:8501`.

## Run

After setup and `.env` configuration, run:

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## Usage

1. Enter a research topic in the chat input (e.g. *"recent advances in quantum computing"*).
2. Wait while the agent performs 2-3 web searches and groups sources by theme.
3. A numbered table of discovered sources appears — tick the ones you want to keep.
4. Click **Approve selected** (or approve all / reject all).
5. The graph resumes and the approved sources are stored in the final state.

---

## Example questions the agent can answer

- "What are the latest breakthroughs in solid-state battery technology in 2025?"
- "Find reliable sources comparing RAG vs fine-tuning for enterprise chatbots."
- "What are the current FDA-approved uses of CRISPR-based therapies?"
- "Collect sources about the impact of AI copilots on developer productivity."
- "What are the best practices for securing LangChain/LangGraph apps in production?"

---

## Tech stack

| Library | Role |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful agent graph with Human-in-the-Loop |
| [LangChain](https://github.com/langchain-ai/langchain) | LLM abstractions |
| [langchain-groq](https://pypi.org/project/langchain-groq/) | Groq LLM integration |
| [langchain-tavily](https://pypi.org/project/langchain-tavily/) | Tavily web search tool |
| [Streamlit](https://streamlit.io/) | Browser UI |
| [Rich](https://github.com/Textualize/rich) | Pretty terminal output (CLI mode) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | `.env` secret loading |

---
## License

This project is licensed under the [MIT License](LICENSE).
