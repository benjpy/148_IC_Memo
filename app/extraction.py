import os
import google.generativeai as genai
from .cost_tracker import CostTracker

class ExtractionEngine:
    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: str, cost_tracker: CostTracker):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.MODEL_NAME)
        self.cost_tracker = cost_tracker

    def _generate_content(self, prompt_parts: list) -> str:
        """
        Helper to call Gemini and track costs.
        """
        try:
            # Count input tokens (approximated or using count_tokens API if strictly needed, 
            # but usually we just calculate cost after generation if the response object has usage metadata.
            # Gemini Python SDK response objects usually have usage_metadata).
            
            response = self.model.generate_content(prompt_parts)
            
            # Extract token usage from response if available
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                self.cost_tracker.add_tokens(input_tokens, output_tokens)
            
            return response.text.strip()
        except Exception as e:
            return f"[Error in generation: {e}]"

    def extract_all(self, processed_files: list) -> dict:
        """
        Main extraction method.
        """
        # Prepare context from files
        context_parts = ["You are an expert VC analyst assistant. Extract information for an IC Memo based on the following files.\n"]
        
        text_context = ""
        images = []

        for file_data in processed_files:
            if file_data["type"] == "text":
                text_context += f"\n{file_data['content']}\n"
            elif file_data["type"] == "image":
                images.append(file_data["content"])
                context_parts.append(f"\n[Image: {file_data['name']}]\n")
                context_parts.append(file_data["content"])

        context_parts.append(text_context)

        # We can do one big call or separate calls. 
        # For better accuracy, separate calls for each section are often better, 
        # but expensive on context window if we re-send everything. 
        # Fortunately Gemini Flash has a large context window and is cheap.
        # Let's do one big structured extraction to JSON for efficiency and consistency.
        
        prompt = """
        Based on the provided documents, extract the following information. 
        If information is missing, explicitly state "Unknown".
        
        Output must be in valid JSON format with the following keys:
        - company_name: The name of the company.
        - business_description: A concise, neutral VC-style business description (1-2 sentences).
        - cost: Total cost of investment.
        - fmv: Current Fair Market Value (FMV).
        - equity_percent: Current equity percentage held.
        - valuation_basis: The basis for current valuation (e.g., Last Round, Note conversion).
        - total_raised: Total amount raised by the company to date.
        - sosv_initial_investment_year: The year (YYYY) of SOSV's initial investment.
        - fundraising_history: A text table with columns: Date | Funds | Category | Type & Series | Amt Raised.

        Ensure the tone is professional and objective.
        
        Example Output:
        {
            "company_name": "Acme Corp",
            "business_description": "Acme Corp is a logistics platform...",
            "cost": "$100,000",
            "fmv": "$500,000",
            "equity_percent": "5.2%",
            "valuation_basis": "Series A",
            "total_raised": "$12.5M",
            "sosv_initial_investment_year": "2021",
            "fundraising_history": "Date | Funds | Category | Type & Series | Amt Raised\\n2021-01 | Fund I | Seed | Equity Seed | $2M\\n..."
        }
        """
        context_parts.append(prompt)
        
        # We need to enforce JSON. 
        # Gemini often returns markdown code blocks ```json ... ```.
        # We'll use generation_config to ask for JSON if supported or just parse it.
        # Flash supports response_mime_type="application/json".
        
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )

        try:
            response = self.model.generate_content(context_parts, generation_config=generation_config)
            
            # Tracking
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                self.cost_tracker.add_tokens(input_tokens, output_tokens)
                
            import json
            return json.loads(response.text)
        except Exception as e:
            return {
                "company_name": "Error extracting",
                "business_description": f"Error: {e}",
                "fundraising_history": "Error"
            }
