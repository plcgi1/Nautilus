/* globals artifacts */
const mytoken = artifacts.require('MyToken')

module.exports = function(deployer) {
    deployer.deploy(mytoken)
}
