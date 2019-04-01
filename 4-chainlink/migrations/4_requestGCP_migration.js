var Oracle = artifacts.require("Oracle");
var GcpService = artifacts.require("requestGCP");

module.exports = (deployer, network, accounts) => {
  const oracleAddress = Oracle.address
  deployer.deploy(GcpService, oracleAddress, {from: accounts[0]});
};
