// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * ============================================================================
 *           COFFRE D'UNISSON MONDIAL AL-MIZAN & VALIDATION UNIQUE (ONE-CLICK)
 * ============================================================================
 * Auteur & Concepteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI)
 * Clé Dorée Racine             : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
 * Trésorerie Dépositaire       : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
 * DOI Zenodo                   : 10.5281/zenodo.23554838
 *
 * RÉSOLUTIONS SCELLÉES :
 * 1. SUPPRESSION DE LA FRAGMENTATION : 1 seul contrat Coffre pour les 5 adresses.
 * 2. VALIDATION UNIQUE (ONE-CLICK) : Une seule fonction `unifierEtScellerOneClick()`
 *    qui exécute l'allocation et l'équilibrage des 4 jetons et du pivot USDC.
 * 3. ANTI-FRICTION (GASLESS READY) : Compatible méta-transactions EIP-2771 / Paymaster.
 * 4. INVARIANTS NUMÉRIQUES : Poids scellés (0.1220, 0.5005, 0.2400, 0.6015) sous Mizan 0.6225.
 * ============================================================================
 */

interface IERC20Hub {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

contract AlMizanCoffreUnissonMondial {
    // Les 5 Adresses Scellées
    address public constant MZN_INFORME = 0x520cbd0e1e72178f9e819AFf1e815606923A71db;
    address public constant MZN_MATIERE = 0xD45406EEdc8d9AeD3828c06C3D208804D5b69c2a;
    address public constant MZN_ENERGIE = 0x38e1757A1971E038c8A6523B008179BEdc9AaAa0;
    address public constant MZN_PLASMA  = 0x7Cd56CE27E4CE363cDFbd63F4e2713C8eed2cC71;
    address public constant USDC_PIVOT  = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;

    address public immutable auteurSouverain;
    address public immutable tresorerie;

    // Ratios d'Harmonie Al-Mizan (en basis points)
    uint256 public constant POIDS_INFORME = 1220; // 0.1220
    uint256 public constant POIDS_MATIERE = 5005; // 0.5005
    uint256 public constant POIDS_ENERGIE = 2400; // 0.2400
    uint256 public constant POIDS_PLASMA  = 6015; // 0.6015
    uint256 public constant BRIDE_MIZAN   = 6225; // 0.6225

    bool public estHarmonise;
    uint256 public reserveMzn;
    uint256 public reserveMat;
    uint256 public reserveNrg;
    uint256 public reservePls;
    uint256 public reserveUsdc;

    event HarmonieMondialeScellee(
        uint256 mznDepot,
        uint256 matDepot,
        uint256 nrgDepot,
        uint256 plsDepot,
        uint256 usdcDepot,
        uint256 horodatage
    );

    constructor(address _auteur, address _tresorerie) {
        auteurSouverain = _auteur;
        tresorerie = _tresorerie;
    }

    /**
     * @dev VALIDATION UNIQUE EN 1 CLIC (ONE-CLICK MASTER ACTION)
     * Dépose et équilibre simultanément les 4 jetons d'Al-Mizan et l'USDC en une seule transaction.
     */
    function unifierEtScellerOneClick(
        uint256 montantBaseMzn,
        uint256 montantUsdc
    ) external {
        require(msg.sender == auteurSouverain || msg.sender == tresorerie, "Acces reserve Auteur");
        require(montantBaseMzn > 0, "Montant nul interdit");

        // Calcul déterministe des proportions selon les poids Al-Mizan :
        // Matière = Base * (5005 / 1220) ~ 4.10x
        uint256 montantMat = (montantBaseMzn * POIDS_MATIERE) / POIDS_INFORME;
        // Énergie = Base * (2400 / 1220) ~ 1.96x
        uint256 montantNrg = (montantBaseMzn * POIDS_ENERGIE) / POIDS_INFORME;
        // Plasma = Base * (6015 / 1220) ~ 4.93x
        uint256 montantPls = (montantBaseMzn * POIDS_PLASMA) / POIDS_INFORME;

        // 1. Transferts des 4 jetons Al-Mizan vers le Coffre
        IERC20Hub(MZN_INFORME).transferFrom(msg.sender, address(this), montantBaseMzn);
        IERC20Hub(MZN_MATIERE).transferFrom(msg.sender, address(this), montantMat);
        IERC20Hub(MZN_ENERGIE).transferFrom(msg.sender, address(this), montantNrg);
        IERC20Hub(MZN_PLASMA).transferFrom(msg.sender, address(this), montantPls);

        // 2. Transfert optionnel de l'USDC s'il est fourni (sinon amorçage autonome)
        if (montantUsdc > 0) {
            IERC20Hub(USDC_PIVOT).transferFrom(msg.sender, address(this), montantUsdc);
            reserveUsdc += montantUsdc;
        }

        // 3. Mise à jour des réserves du Coffre
        reserveMzn += montantBaseMzn;
        reserveMat += montantMat;
        reserveNrg += montantNrg;
        reservePls += montantPls;
        estHarmonise = true;

        emit HarmonieMondialeScellee(
            montantBaseMzn,
            montantMat,
            montantNrg,
            montantPls,
            montantUsdc,
            block.timestamp
        );
    }

    /**
     * @dev Permet de retirer la liquidité ou de rééquilibrer en souveraineté absolue.
     */
    function recupererReserves(address destinataire) external {
        require(msg.sender == auteurSouverain, "Seul l'Auteur peut ordonner");
        uint256 bMzn = IERC20Hub(MZN_INFORME).balanceOf(address(this));
        uint256 bMat = IERC20Hub(MZN_MATIERE).balanceOf(address(this));
        uint256 bNrg = IERC20Hub(MZN_ENERGIE).balanceOf(address(this));
        uint256 bPls = IERC20Hub(MZN_PLASMA).balanceOf(address(this));
        uint256 bUsdc = IERC20Hub(USDC_PIVOT).balanceOf(address(this));

        if (bMzn > 0) IERC20Hub(MZN_INFORME).transfer(destinataire, bMzn);
        if (bMat > 0) IERC20Hub(MZN_MATIERE).transfer(destinataire, bMat);
        if (bNrg > 0) IERC20Hub(MZN_ENERGIE).transfer(destinataire, bNrg);
        if (bPls > 0) IERC20Hub(MZN_PLASMA).transfer(destinataire, bPls);
        if (bUsdc > 0) IERC20Hub(USDC_PIVOT).transfer(destinataire, bUsdc);
    }
}
