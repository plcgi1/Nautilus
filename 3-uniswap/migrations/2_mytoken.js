/* globals artifacts */
const mytoken = artifacts.require('OceanToken')

module.exports = function(deployer) {
    deployer.deploy(mytoken)
}
