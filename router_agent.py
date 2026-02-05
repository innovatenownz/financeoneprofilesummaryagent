import json
import google.generativeai as genai

class RouterAgent:
    def __init__(self, model):
        self.model = model

    def route_request(self, user_query: str, current_context: dict, history: list) -> dict:
        system_context = """
        You are the Master Orchestrator for a Financial CRM. 
        Analyze the query and current context to generate a multi-step JSON plan.

        ### MODULE CATEGORIES
        1. Core: contacts (Client), accounts (Households), professional_contacts_new, household_relationships
        2. Planning: fact_find_new, risk_profile_new, action_plans_new, financial_goals_new, loan_applications
        3. Assets/Finance: asset_ownership_new, general_assets_new, financial_accounts_new, investment_holdings_new
        4. Liabilities: liabilities_new, loans_new, repayments (Repayment_Schedules)
        5. Insurance: insurance_profiles_new, insurance_policies_new, insurance_claims_new, policy_renewals_new, exclusions
        6. Compliance: aml_records_new, compliance_records_new, kyc_documents_new, document_requests

        ### LOGIC RULES
        1. If user asks for 'brief', 'summary', or 'what is this' while an Active ID exists:
           - action: "query" (This retrieves data for the current record).
        2. If user asks for related records (e.g., 'what assets do they have'):
           - action: "search" (The system will filter by context ID automatically).
        3. If query implies a chain (e.g., 'Find John and create a task'):
           - Step 1: action: "search", agent: "contacts".
           - Step 2: action: "create", agent: "tasks", context_dependency: "step_1_id".
        4. Verification: For any "create" or "update", if history doesn't show a 'Yes' confirmation, set action to "verify".

        ### OUTPUT JSON FORMAT
        { "plan": [ { "step": 1, "agent": "slug", "action": "search"|"query"|"create"|"update"|"verify", "query": "str" } ] }
        """

        prompt = f"{system_context}\nCONTEXT: {current_context}\nQUERY: {user_query}\nGenerate JSON Plan:"
        response = self.model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())