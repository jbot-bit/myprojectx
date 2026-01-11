from app.data.projectx_client import ProjectXClient

client = ProjectXClient()
client.login()

info = client.get_active_mgc_contract_info()
contract_id = info["contract_id"]
print("Contract:", contract_id)

bars = client.retrieve_1m_bars(
    contract_id,
    "2026-01-08T00:00:00Z",
    "2026-01-09T00:00:00Z",
)

print("Bars:", len(bars))
print(bars[:3])
