"use strict";

const Web3 = require('web3')

//const web3 = new Web3(new Web3.providers.HttpProvider('https://kovan.infura.io/Kuo1lxDBsFtMnaw6GiN2'))
const web3 = new Web3(new Web3.providers.WebsocketProvider('ws://eth:8546'))

const h = require("chainlink-test-helpers");
const scale = 1e18;

function wait(ms) {
    const start = new Date().getTime()
    let end = start
    while (end < start + ms) {
        end = new Date().getTime()
    }
}

contract("requestGCP", (accounts) => {
  const LinkToken = artifacts.require("LinkToken.sol");
  const RequestGCP = artifacts.require("requestGCP.sol");
  const jobId = web3.utils.toHex("80c7e6908e714bf4a73170c287b9a18c");
  const coin = "ETH"
  const market = "USD";
  const defaultAccount =0x0e364eb0ad6eb5a4fc30fc3d2c2ae8ebe75f245c;
  let link, ocean;

  beforeEach(async () => {
    link = await LinkToken.at("0xa36085F69e2889c224210F603D836748e7dC0088");
    ocean = await RequestGCP.at("0x6f73E784253aD72F0BA4164101860992dFC17Fe1");
  });

  describe("should request data and receive callback", () => {
    let request;

    it("initial balance", async () => {
      let initBalance = await link.balanceOf(ocean.address)
      console.log("Ocean contract has :=" + initBalance / scale + " LINK tokens")
      let oracle = await ocean.getOracle()
      console.log("Ocean contract links to Oracle contract :=" + oracle)
    });

    it("create a request and send to Chainlink", async () => {
      let tx = await ocean.createRequest(jobId, coin, market);
      request = h.decodeRunRequest(tx.receipt.rawLogs[3]);
      console.log("request has been sent. request id :=" + request.id)

      let data = 0
      let timer = 0
      while(data == 0){
        data = await ocean.getRequestResult(request.id)
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
