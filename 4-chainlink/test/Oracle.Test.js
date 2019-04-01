"use strict";

const Web3 = require('web3')

const web3 = new Web3(new Web3.providers.HttpProvider('https://kovan.infura.io/Kuo1lxDBsFtMnaw6GiN2'))


const h = require("chainlink-test-helpers");
const scale = 1e18;

contract("Oracle", (accounts) => {
  const Oracle = artifacts.require("Oracle.sol");
  const chainlinkNode ='0x79B80f3b6B06FD5516146af22E10df26dfDc5455';
  let oracle;

  beforeEach(async () => {
    oracle = await Oracle.at("0x698EFB00F79E858724633e297d5188705512e506");
  });

  describe("should register chainlink node", () => {

    it("register chainlink node", async () => {
      await oracle.setFulfillmentPermission(chainlinkNode, true)
      let status = await oracle.getAuthorizationStatus(chainlinkNode)
      console.log("Chainlink node's status is := " + status)
    });
  });
});
