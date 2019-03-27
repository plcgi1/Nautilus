const HDWalletProvider = require('truffle-hdwallet-provider')
var mnemonic = process.env.NMEMORIC


module.exports = {
    networks: {
        development: {
            host: 'localhost',
            port: 8545,
            network_id: '*',
            gas: 6000000
        },
        // Rinkeby testnet
        rinkeby: {
            provider: function() {
              return new HDWalletProvider(process.env.NMEMORIC, "https://rinkeby.infura.io/Kuo1lxDBsFtMnaw6GiN2")
            },
            network_id: '4',
            gas: 6000000,
            gasPrice: 10000000000 // 10 Gwei
        },
    },
    compilers: {
        solc: {
            version: '0.5.3',
            settings: {
                optimizer: {
                    enabled: true,
                    runs: 200
                }
            }
        }
    }
}
