import json

class UserData:

    def __init__(self):
        self.user_data_map = {
            "client_1": {
                "date_of_birth_spouse_1": "1955-06-15",
                "date_of_birth_spouse_2": "1957-09-22",
                "end_of_year_account_balance": 3345000.50,
                "marital_status": "Married Filing Jointly",
                "retirement_age_spouse_1": 65,
                "current_income_spouse_1": 780000,
                "retirement_age_spouse_2": 65,  # Included as requested
                "current_income_spouse_2": 550000,   # Included as requested
                "self_employed_spouse_1": True,
                "self_employed_spouse_2": False
            },
            "client_2": {
                "date_of_birth_spouse_1": "1985-06-15",
                "date_of_birth_spouse_2": "1987-09-22",
                "end_of_year_account_balance": 245000.50,
                "marital_status": "Married Filing Jointly",
                "retirement_age_spouse_1": 65,
                "current_income_spouse_1": 120000,
                "retirement_age_spouse_2": 65,  # Included as requested
                "current_income_spouse_2": 120000,   # Included as requested
                "self_employed_spouse_1": False,
                "self_employed_spouse_2": False
            },
            "client_3": {
                "date_of_birth_spouse_1": "1985-06-15",
                "date_of_birth_spouse_2": "1987-09-22",
                "end_of_year_account_balance": 245000.50,
                "marital_status": "Single",
                "retirement_age_spouse_1": 65,
                "current_income_spouse_1": 120000,
                "self_employed_spouse_1": False,
            }
        }   


    def get_user_data(self, client_id: str) -> str:
        """Returns a dummy JSON string with user financial information."""

        user_data = self.user_data_map.get(client_id)
        if not user_data:
            raise ValueError(f"Client ID {client_id} not found.")
        return json.dumps(user_data, indent=4)  

