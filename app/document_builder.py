from googleapiclient.discovery import build

class DocumentBuilder:
    def __init__(self, credentials):
        """
        Initializes with OAuth 2.0 Credentials.
        """
        self.creds = credentials

    def create_memo(self, data: dict) -> str:
        """
        Creates a Google Doc with strict formatting using OAuth credentials.
        Returns the URL of the created document.
        """
        if not self.creds:
            return "Error: No credentials provided. Please login."

        try:
            service = build('docs', 'v1', credentials=self.creds)
            
            # 1. Create Document
            company_name = data.get('company_name', 'Draft')
            title = f"IC Memo - {company_name}"
            body = {'title': title}
            doc = service.documents().create(body=body).execute()
            doc_id = doc.get('documentId')

            # 2. Prepare content
            c_name = data.get('company_name', 'Unknown')
            b_desc = data.get('business_description', 'Unknown')
            f_hist = data.get('fundraising_history', 'Unknown')
            
            # Additional Metrics
            metrics_block = (
                f"Cost: {data.get('cost', 'Unknown')}\n"
                f"FMV: {data.get('fmv', 'Unknown')}\n"
                f"Equity %: {data.get('equity_percent', 'Unknown')}\n"
                f"Valuation Basis: {data.get('valuation_basis', 'Unknown')}\n"
                f"Total $ Raised: {data.get('total_raised', 'Unknown')}\n"
                f"SOSV Initial Investment Year: {data.get('sosv_initial_investment_year', 'Unknown')}"
            )

            requests = []

            # Helper to generate requests for a section
            # We insert in reverse order (bottom to top) always at index 1.
            # This ensures the newest inserted section is at the top, pushing others down.
            def create_section_requests(header, content):
                full_text = f"{header}\n{content}\n\n"
                header_len = len(header)
                
                # 1. Insert Text at Index 1
                insert_req = {
                    'insertText': {
                        'location': {'index': 1},
                        'text': full_text
                    }
                }
                
                # 2. Format Header (Bold, Uppercase, 14pt) - Range is from 1 to 1+header_len
                # Note: We assume header is already uppercased string passed in
                header_style_req = {
                    'updateTextStyle': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': 1 + header_len
                        },
                        'textStyle': {
                            'bold': True,
                            'fontSize': {'magnitude': 14, 'unit': 'PT'}
                        },
                        'fields': 'bold,fontSize'
                    }
                }

                # 3. Format Body (Normal, 11pt) - Range is after header to end of inserted text
                body_style_req = {
                    'updateTextStyle': {
                        'range': {
                            'startIndex': 1 + header_len + 1, # +1 for newline
                            'endIndex': 1 + len(full_text)
                        },
                        'textStyle': {
                            'bold': False,
                            'fontSize': {'magnitude': 11, 'unit': 'PT'}
                        },
                        'fields': 'bold,fontSize'
                    }
                }
                
                return [insert_req, header_style_req, body_style_req]

            # 3. Build Request Queue (Reverse Order)
            # Desired Final Order:
            # 1. COMPANY NAME
            # 2. INVESTMENT SNAPSHOT
            # 3. BUSINESS DESCRIPTION
            # 4. FUNDRAISING HISTORY
            
            # So we insert: 4 -> 3 -> 2 -> 1
            
            requests.extend(create_section_requests("FUNDRAISING HISTORY", f_hist))
            requests.extend(create_section_requests("BUSINESS DESCRIPTION", b_desc))
            requests.extend(create_section_requests("INVESTMENT SNAPSHOT", metrics_block))
            requests.extend(create_section_requests("COMPANY NAME", c_name))

            # 4. Execute Batch Update
            service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
            return f"https://docs.google.com/document/d/{doc_id}/edit"

        except Exception as e:
            return f"Error creating doc: {e}"
