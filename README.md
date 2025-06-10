# 🧠 Most Popular Smart Contracts with Safe Wallets

This project identifies the most frequently interacted-with smart contracts by **Safe wallets**, using data sourced from **Dune Analytics**.

## 🔧 How It Works

The main script `top_contracts.py` retrieves interaction data from Dune. Labels for Ethereum addresses are sourced from:

- [eth-labels GitHub repo](https://github.com/dawsbot/eth-labels)

Alternatively, Etherscan’s Labels API could be used, but it's a **paid Pro API**. Some labels are publicly available for free.

---

## ▶️ To Reproduce

1. **Set environment variables** in your `.env` file:

   - `DUNE_API_KEY`
   - `TOP_CONTRACTS_QUERY`
   - `ETHERSCAN_API_KEY`
   - `ETHEREUM_RPC_URL`

2. **Run the following scripts in order:**
   - `top_contracts.py`: Fetch data from Dune.
   - `etherscan.py`: Retrieve contract labels using the Etherscan API.
   - `get_symbols.py`: Get token symbols via Ethereum JSON-RPC.
   - `custom_label.py`: Apply custom labels using the `eth_labels` CSV files.
   - `filter_protocols.py`: Filter out non-ERC20 tokens from the list.

---

## 📊 Top 10 Protocols by Safe Transaction Volume

| Rank | Protocol         | Total Interactions | Key Contracts                                                                                                  |
| ---- | ---------------- | ------------------ | -------------------------------------------------------------------------------------------------------------- |
| 1    | **Uniswap**      | 48,630             | NonfungiblePositionManager, SwapRouter02, UniswapV2Router02, UniversalRouter, SwapRouter                       |
| 2    | **Cow Protocol** | 42,181             | GPv2Settlement                                                                                                 |
| 3    | **ENS**          | 18,892             | ETHRegistrarController, PublicResolver, ReverseRegistrar, ENSRegistryWithFallback, BaseRegistrarImplementation |
| 4    | **KuCoin**       | 8,235              | ERC1967Proxy                                                                                                   |
| 5    | **1inch**        | 7,342              | AggregationRouterV3, AggregationRouterV4, AggregationRouterV5                                                  |
| 6    | **Aave**         | 6,181              | InitializableImmutableAdminUpgradeabilityProxy                                                                 |
| 7    | **Gnosis Safe**  | 5,424              | Airdrop                                                                                                        |
| 8    | **Sushiswap**    | 4,260              | UniswapV2Router02                                                                                              |
| 9    | **Balancer**     | 3,179              | Vault                                                                                                          |
| 10   | **Sablier**      | 2,751              | Sablier                                                                                                        |

---

## 📝 Notes

- **KuCoin (8,235 transactions)**: Interactions occur via a proxy contract. As a **centralized exchange**, it’s not considered a DeFi protocol and is excluded from rankings that compare only DeFi protocols.
- **Protocols like Safe or ENS** are included for completeness even though they serve broader infrastructure purposes beyond just DeFi.
# safe-top-protocols
