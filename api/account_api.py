class AccountApi:
    def __init__(self, api_client):
        self.api = api_client

    async def get_balance(self, account_id: int):
        return await self.api.get(f"/accounts/{account_id}/balance")
