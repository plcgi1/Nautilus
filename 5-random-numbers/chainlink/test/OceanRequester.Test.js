"use strict";

const Web3 = require('web3')

const web3 = new Web3(new Web3.providers.HttpProvider('https://rinkeby.infura.io/Kuo1lxDBsFtMnaw6GiN2'))

const h = require("chainlink-test-helpers");
const scale = 1e18;

function wait(ms) {
    const start = new Date().getTime()
    let end = start
    while (end < start + ms) {
        end = new Date().getTime()
    }
}

contract("OceanRequester", (accounts) => {
  const LinkToken = artifacts.require("LinkToken.sol");
  const OceanRequester = artifacts.require("OceanRequester.sol");
  const defaultAccount =0x0e364eb0ad6eb5a4fc30fc3d2c2ae8ebe75f245c;
  const LINK_FEE = web3.utils.toHex(1*10**18)
  const LB = web3.utils.toHex(100)
  const UB = web3.utils.toHex(1000)
  let link, ocean;

  beforeEach(async () => {
    link = await LinkToken.at("0x01BE23585060835E02B77ef475b0Cc51aA1e0709");
    ocean = await OceanRequester.at("0x81C8A4BE1bf2491D3c90BdE4615EE4672F13E63b");
  });

  describe("should request data and receive callback", () => {
    let request;

    it("transfer 1 LINK token to Ocean requester contract if there is no any", async () => {
      let balance = await link.balanceOf(ocean.address)
      if (balance == 0) {
        await link.transfer(ocean.address, LINK_FEE)
      }
    });


    it("LINK balance", async () => {
      let initBalance = await link.balanceOf(ocean.address)
      console.log("Ocean contract has :=" + initBalance / scale + " LINK tokens")
    });

    it("create a request and send to Chainlink", async () => {
      let tx = await ocean.getRandom(LB, UB);
      request = h.decodeRunRequest(tx.receipt.rawLogs[3]);
      console.log("request has been sent. request id :=" + request.id)

      let data = 0
      let timer = 0
      while(data == 0){
        data = await ocean.getRequestResult()
        if(data != 0) {
          console.log("Request is fulfilled. data := " + data)
        }
        wait(1000)
        timer = timer + 1
        console.log("waiting for " + timer + " second")
      }

    });
  });
});
