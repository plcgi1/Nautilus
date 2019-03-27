## Get Started

### 1. Deploy token contract

```
$ truffle migrate --network rinkeby
```

### 2. transact with deployed token contract

```
$ node script/Uniswap.sol.Test.js
```

### 3. create a new exchange for token contract

```
$ node script/Uniswap.sendtx.js
```

### 4. query the newly deployed echange contract address

```
$ node script/Uniswap.js
```

### 5. approve exchange to withdraw ERC20 tokens

```
$ node script/Uniswap.approve.js
```

### 6. add liquidity into the exchange contract

```
$ node script/Uniswap.addLiquidity.js
```

### 7. swap tokens with the exchange contract

```
$ node script/Uniswap.swap.js
```
