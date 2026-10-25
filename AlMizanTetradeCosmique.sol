// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * ============================================================================
 *               TÉTRADE COSMIQUE AL-MIZAN & HUB LIQUIDITÉ USDC
 * ============================================================================
 * Auteur & Créateur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI)
 * Clé Dorée Racine           : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
 * Trésorerie Dépositaire     : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
 * DOI Zenodo                 : 10.5281/zenodo.23554838
 *
 * ARCHITECTURE DES 4 JETONS COSMIQUES DE LA TÉTRADE :
 * 1. MZN (Informé)  : 0x520cbd0e1e72178f9e819AFf1e815606923A71db (Déployé)
 * 2. MZN-MAT (Matière) : Die Silicium, Or Z=79, Argent Z=47, 27 Formes (0.5005)
 * 3. MZN-NRG (Énergie) : Hydro 313 L/min, Wattmètre 47.7W, Cryo 22.5 mK (0.2400)
 * 4. MZN-PLS (Plasma)  : Ionisation libre, Pulsation micro-onde, CPMG (0.6015)
 *
 * PIVOT CENTRAL DE STABILITÉ : USDC Natif Base (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
 * ============================================================================
 */

interface IERC20Minimal {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

/**
 * @dev Implémentation souveraine standard d'un token pilier de la Tétrade.
 */
contract AlMizanPilierToken {
    string public name;
    string public symbol;
    uint8 public constant decimals = 18;
    uint256 public immutable totalSupply;
    uint256 public immutable poidsOntologiqueBps; // Ex: 5005 pour Matière, 2400 pour Énergie, 6015 pour Plasma
    
    address public immutable createurAuteur;
    address public immutable tresorerie;

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _poidsBps,
        address _cleAuteur,
        address _tresorerie
    ) {
        require(_cleAuteur != address(0) && _tresorerie != address(0), "Adresses invalides");
        name = _name;
        symbol = _symbol;
        poidsOntologiqueBps = _poidsBps;
        createurAuteur = _cleAuteur;
        tresorerie = _tresorerie;

        // Supply identique scellée à 313 000 000 jetons (Constante C = 313)
        totalSupply = 313_000_000 * 10**18;

        // Répartition conforme Al-Mizan : 302M en réserve clé dorée + 11M en trésorerie
        uint256 reserve = 302_000_000 * 10**18;
        uint256 exploitation = 11_000_000 * 10**18;

        _balances[createurAuteur] = reserve;
        _balances[tresorerie] = exploitation;

        emit Transfer(address(0), createurAuteur, reserve);
        emit Transfer(address(0), tresorerie, exploitation);
    }

    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(_balances[msg.sender] >= value, "Solde insuffisant");
        _balances[msg.sender] -= value;
        _balances[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function allowance(address owner, address spender) external view returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 value) external returns (bool) {
        _allowances[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = _allowances[from][msg.sender];
        require(allowed >= value, "Allowance insuffisante");
        require(_balances[from] >= value, "Solde insuffisant");
        if (allowed != type(uint256).max) {
            _allowances[from][msg.sender] = allowed - value;
        }
        _balances[from] -= value;
        _balances[to] += value;
        emit Transfer(from, to, value);
        return true;
    }
}
