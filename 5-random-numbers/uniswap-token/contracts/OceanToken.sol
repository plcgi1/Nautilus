pragma solidity 0.5.3;

import 'openzeppelin-solidity/contracts/token/ERC20/ERC20Capped.sol';
import 'openzeppelin-solidity/contracts/token/ERC20/ERC20Detailed.sol';
import 'openzeppelin-solidity/contracts/ownership/Ownable.sol';

/**
 * @title Ocean Protocol ERC20 Token Contract
 * @author Ocean Protocol Team
 *
 * @dev Implementation of the Ocean Token.
 */
contract OceanToken is Ownable, ERC20Detailed, ERC20Capped {

	using SafeMath for uint256;

	uint256 CAP = 1410000000;
	uint256 TOTALSUPPLY = CAP.mul(10 ** 18);

	/**
	* @dev OceanToken constructor
	*      Runs only on initial contract creation.
	*/
	constructor()
		public
		ERC20Detailed('OceanToken', 'OCEAN', 18)
		ERC20Capped(TOTALSUPPLY)
		Ownable()
	{
		_mint(msg.sender, TOTALSUPPLY);
	}

}
