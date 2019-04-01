/* globals artifacts */
const OceanToken = artifacts.require('OceanToken')

module.exports = function(deployer) {
    deployer.deploy(OceanToken)
}
