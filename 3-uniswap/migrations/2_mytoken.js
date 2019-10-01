/* globals artifacts */
const mytoken = artifacts.require('EarthToken')

module.exports = function(deployer) {
    deployer.deploy(mytoken)
}
