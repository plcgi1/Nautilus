var oracle = artifacts.require("Oracle");

const linkToken = '0xa36085F69e2889c224210F603D836748e7dC0088'

module.exports = (deployer, network, accounts) => {
  deployer.deploy(oracle, linkToken, {from: accounts[0]});
};
