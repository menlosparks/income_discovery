import os
import json
from bs4 import BeautifulSoup
import anthropic


class ClaudeFileSearcher:
    """
    A file searcher that uses the Anthropic Claude API.
    Mirrors the interface of FileSearcher but uses Claude for generation
    and reads files locally instead of uploading to a remote store.
    """

    MODEL = "claude-sonnet-4-5"

    SYSTEM_INSTRUCTION = """
    You are a helpful financial advisor. Give concise answers to the user's questions. Limit
    the answers to 3 or 4 sentences. If the answer is not in the documents, say so. Be very sure of 
    your calculations and provide the answer in a clear and concise manner. Do not 
    exceed 100 words in your response. 
    You have access to the `get_dummy_user_data` tool to retrieve information about the user's 
    spouse, income, and account balances. Use it whenever a question requires specific user data.
    """

    # Tool definition for Claude's tool_use feature
    TOOLS = [
        {
            "name": "get_dummy_user_data",
            "description": "Returns a JSON object with user financial information including "
                           "spouse dates of birth, account balance, marital status, "
                           "retirement ages, and income.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]

    def __init__(self, files_list: list[str]):
        """
        Args:
            files_list: List of file paths to load and search.
        """
        self.files_list = files_list
        self.file_search_store = None  # Holds in-memory parsed document text
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def _read_file(self, filepath: str) -> str:
        """Read and extract plain text from an HTML or plain text file."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        ext = os.path.splitext(filepath)[1].lower()
        if ext in (".html", ".htm"):
            soup = BeautifulSoup(raw, "lxml")
            return soup.get_text(separator="\n", strip=True)
        return raw

    def upload_files(self):
        """
        'Upload' files — reads and caches document text in memory.
        Returns a dict acting as a pseudo file-search store.
        """
        print("Loading files into memory (Claude does not use a remote file store)...")
        documents = {}
        for filepath in self.files_list:
            name = os.path.basename(filepath)
            print(f"  Reading: {name}...")
            documents[name] = self._read_file(filepath)
            print(f"  Loaded {name} ({len(documents[name])} characters).")

        self.file_search_store = documents
        print(f"All {len(documents)} file(s) loaded.")
        return self.file_search_store

    def search_files(self, query: str):
        """
        Search files using Claude. Injects loaded document text as context
        and supports tool_use for get_dummy_user_data.
        Returns an object with a .text attribute for compatibility with main.py.
        """
        if not self.file_search_store:
            raise RuntimeError("Call upload_files() before search_files().")

        # Build context block from all documents
        doc_context = "\n\n".join(
            f"=== Document: {name} ===\n{text}"
            for name, text in self.file_search_store.items()
        )

        user_message = (
            f"Use the following documents as your knowledge base:\n\n"
            f"{doc_context}\n\n"
            f"User question: {query}"
        )

        messages = [{"role": "user", "content": user_message}]

        # Agentic loop to handle tool_use responses
        while True:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1024,
                system=self.SYSTEM_INSTRUCTION,
                tools=self.TOOLS,
                messages=messages,
            )

            # If Claude wants to call a tool, execute it and continue the loop
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_use_id = block.id
                        if tool_name == "get_dummy_user_data":
                            result = self.get_dummy_user_data()
                        else:
                            result = json.dumps({"error": f"Unknown tool: {tool_name}"})

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })

                # Append Claude's tool_use turn and our tool results
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            else:
                # Final text response — wrap it for compatibility with main.py (.text attribute)
                return _ClaudeResponse(response)

    def get_dummy_user_data(self) -> str:
        """Returns a dummy JSON string with user financial information."""
        user_data = {
            "date_of_birth_spouse_1": "1985-06-15",
            "date_of_birth_spouse_2": "1987-09-22",
            "end_of_year_account_balance": 245000.50,
            "marital_status": "Married Filing Jointly",
            "retirement_age_spouse_1": 65,
            "current_income_spouse_1": 120000,
            "retirement_age_spouse_2": 67,
            "current_income_spouse_2": 95000
        }
        return json.dumps(user_data, indent=4)


class _ClaudeResponse:
    """
    Thin wrapper around an Anthropic message response.
    Provides a .text property so callers can use `response.text`
    the same way as with the Gemini SDK.
    """

    def __init__(self, response):
        self._response = response

    @property
    def text(self) -> str:
        """Extract the first text block from Claude's response content."""
        for block in self._response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def __repr__(self):
        return f"<ClaudeResponse text={self.text[:80]!r}>"
