var oceanRequester = artifacts.require("OceanRequester");

module.exports = (deployer, network, accounts) => {
  deployer.deploy(oceanRequester, {from: accounts[0]});
};
