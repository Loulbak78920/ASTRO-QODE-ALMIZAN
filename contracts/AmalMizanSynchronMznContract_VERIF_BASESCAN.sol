// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * ============================================================================
 *                    AMAL-MIZAN SYNCHRON MZN SMART CONTRACT
 * ============================================================================
 * Auteur & Createur Officiel : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
 * Date de Naissance         : 20 juin 1989 (20/06/1989) a Meulan-en-Yvelines (78, France)
 * Contact Email             : elbahloulahmed505[at]gmail.com
 * Cle Doree Souveraine      : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
 * Tresorerie Privee Auteur  : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
 * DOI Zenodo Officiel Reel  : 10.5281/zenodo.23554838
 * Depot GitHub Officiel     : https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN
 *
 * FONDEMENTS & INVARIANTS SCELLES :
 * 1. Token MZN Souverain (ERC-20 etendu) :
 *    - Volume d'emission totale (Supply) : 313 000 000 MZN (Constante C = 313)
 *    - Decimales : 18
 *    - Anti-Usure Absolue (Anti-Riba) : 0% usure, 0% interet, creation fractionnaire bannie.
 * 2. Registre des Actes & Sceaux Scelles :
 *    - Sceaux immuables des actes (A001 a A074...) sous hash SHA-256 scelle.
 * 3. Invariants Metrologiques Al-Mizan :
 *    - MIZAN_BPS = 6225 (0.6225 ou 62.25%)
 *    - LIGNE_REF_BPS = 1220 (0.122)
 *    - EPSILON_BPS = 210 (0.021)
 *    - PLAFOND_BPS = 6015 (0.6015)
 *    - omniscienceClaim = false
 *    - allahHorsMatrice = true
 *    - qubitPhysiqueLocal = false
 * 4. Contrat Commercial 50/50 & Licence Anti-Dolosive :
 *    - Partage egalitaire 50% Auteur / 50% Exploitant sur toute valorisation commerciale.
 *    - Revocation immediate en cas de dissimulation d'auteur, fraude ou bris de garde-fous.
 * 5. Module Fiscal de Purification :
 *    - Zakat : 2.5% (1/40, soit 250 bps) obligatoire sur reserve stagnante au-dessus du Nisab.
 *    - Sadaqa : Transfert volontaire sans contrainte a friction zero (0%).
 * 6. Liens Metrologiques Or / Argent & Kernel Temporel :
 *    - Or (Au, Z=79, Nisab 85g Au), Argent (Ag, Z=47, Nisab 595g Ag).
 *    - Horloge Kernel dt = 135097021.3359375 (dx=50027.8359375 + dy=46993.5 + dz=135000000.0).
 * ============================================================================
 */

interface IERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 value) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

interface IERC2981 {
    function royaltyInfo(uint256 tokenId, uint256 salePrice)
        external
        view
        returns (address receiver, uint256 royaltyAmount);
}

contract AmalMizanSynchronMznContract is IERC20, IERC2981 {
    // --- METADONNEES DE L'AUTEUR & DOI ---
    string public constant AUTEUR = "M. Ahmed EL BAHLOUL";
    string public constant AUTEUR_ALIAS = "IMAM8MAHDI / M. Almizan Elbahloul";
    string public constant AUTEUR_EMAIL = "elbahloulahmed505@gmail.com";
    address public constant CLE_DOREE_AUTEUR = 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B;
    address public constant TRESORERIE_PRIVEE_AUTEUR = 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C;
    string public constant DOI_ZENODO_OFFICIEL = "10.5281/zenodo.23554838";

    // --- IDENTITE DU TOKEN MZN (ERC-20) ---
    string public constant name = "Al-Almizan Token Souverain";
    string public constant symbol = "MZN";
    uint8 public constant decimals = 18;
    uint256 public constant CONSTANTE_C = 313;
    uint256 public constant CONSTANTE_M = 24434;
    uint256 public constant TOTAL_SUPPLY = 313_000_000 * 10**18;

    // --- INVARIANTS NUMERIQUES SCELLES (Base 10000 = 100%) ---
    uint256 public constant MIZAN_BPS = 6225;     // 0.6225
    uint256 public constant LIGNE_REF_BPS = 1220; // 0.1220
    uint256 public constant EPSILON_BPS = 210;    // 0.0210
    uint256 public constant PLAFOND_BPS = 6015;   // 0.6015
    uint256 public constant ZAKAT_BPS = 250;      // 2.50% (1/40)

    // --- KERNEL TEMPOREL EXACT SCALE (x 10^7) ---
    // dt = 135097021.3359375 => scale 10^7 : 1350970213359375
    uint256 public constant KERNEL_DT_SCALED = 1350970213359375;
    uint256 public constant KERNEL_DX_SCALED = 500278359375;
    uint256 public constant KERNEL_DY_SCALED = 469935000000;
    uint256 public constant KERNEL_DZ_SCALED = 1350000000000000;

    // --- METROLOGIE DE L'UNISSON OR / ARGENT ---
    uint256 public constant NISAB_OR_GRAMMES = 85;      // 85g Au (20 Mithqals)
    uint256 public constant NISAB_ARGENT_GRAMMES = 595; // 595g Ag (200 Dirhams)
    uint256 public constant NISAB_LOGIQUE_MZN = 668_255 * 10**18; // 2.135 * 313 * 1000

    // --- GARDE-FOUS DE RIGUEUR ET DE SINCERITE ---
    bool public constant omniscienceClaim = false;
    bool public constant allahHorsMatrice = true;
    bool public constant qubitPhysiqueLocal = false;
    bool public constant antiUsureActive = true;

    // --- ADRESSES INSTITUTIONNELLES DES TROIS CITES & RESERVE ---
    address public immutable citePcTerrestre;
    address public immutable citeGalaxyMobile;
    address public immutable citeQistasCivique;
    address public immutable fondsSouverainReserve;
    address public caisseZakatCivique;

    // --- ETAT DES BALANCES MZN (ERC-20) ---
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    uint256 public totalMznCirculant;
    uint256 public totalMznReserveEnAttente;

    // --- REGISTRE DES ACTES ET SCEAUX SCELLES ---
    struct SceauActe {
        uint256 acteId;
        string codeActe;
        bytes32 sha256Empreinte;
        uint256 horodatageUtc;
        uint256 epochKernel;
        address detenteur;
        string description;
    }

    uint256 public nextActeId;
    mapping(uint256 => SceauActe) public registreSceaux;

    // --- BLOCS SYNCHRON MZN ENREGISTRES ---
    struct BlocSynchronInfo {
        uint256 height;
        bytes32 blocHash;
        bytes32 prevHash;
        bytes32 merkleRootTxs;
        bytes32 merkleRootSceaux;
        uint256 timestampUtc;
        uint256 dtScaled;
        uint256 balancePc;
        uint256 balanceGalaxy;
        uint256 balanceQistas;
        uint256 wattsLaboScaled;
        uint256 debitHydroLMin;
    }

    uint256 public dernierBlocHeight;
    mapping(uint256 => BlocSynchronInfo) public blocsSynchron;

    // --- EVENEMENTS SPECIFIQUES ---
    event BlocSynchronScelle(uint256 indexed height, bytes32 indexed blocHash, uint256 timestampUtc);
    event ZakatPrelevee(address indexed depuis, address indexed caisse, uint256 montant);
    event SadaqaTransferee(address indexed de, address indexed vers, uint256 montant);
    event ActeScelle(uint256 indexed acteId, string codeActe, bytes32 sha256Empreinte, address beneficiaire);
    event EvolveContinu(uint256 indexed epoch, uint256 epsilonBps);
    event KaffaraPurge(address indexed auteur, uint256 montantBurn);

    // --- MODIFICATEURS ---
    modifier seulementAuteur() {
        require(
            msg.sender == CLE_DOREE_AUTEUR || msg.sender == TRESORERIE_PRIVEE_AUTEUR,
            "Seul l'Auteur legitime ou sa Tresorerie privee peut executer"
        );
        _;
    }

    // --- CONSTRUCTEUR ---
    constructor(
        address _pcTerrestre,
        address _galaxyMobile,
        address _qistasCivique,
        address _fondsReserve,
        address _caisseZakat
    ) {
        require(_pcTerrestre != address(0), "Adresse PC invalide");
        require(_galaxyMobile != address(0), "Adresse Galaxy invalide");
        require(_qistasCivique != address(0), "Adresse Qistas invalide");
        require(_fondsReserve != address(0), "Adresse Fonds Reserve invalide");

        citePcTerrestre = _pcTerrestre;
        citeGalaxyMobile = _galaxyMobile;
        citeQistasCivique = _qistasCivique;
        fondsSouverainReserve = _fondsReserve;
        caisseZakatCivique = (_caisseZakat != address(0)) ? _caisseZakat : _qistasCivique;

        // Allocation scellee des 11 000 000 MZN debloques sous mandat certifie :
        // P1.1 (1M) + P1.2 (2M) => PC Terrestre (3 000 000 MZN)
        // P2.1 (8M) => Galaxy Mobile (8 000 000 MZN)
        uint256 allocPc = 3_000_000 * 10**18;
        uint256 allocGalaxy = 8_000_000 * 10**18;
        uint256 circulantInitial = allocPc + allocGalaxy; // 11 000 000 MZN
        uint256 reserveInitiale = TOTAL_SUPPLY - circulantInitial; // 302 000 000 MZN

        _balances[citePcTerrestre] = allocPc;
        _balances[citeGalaxyMobile] = allocGalaxy;
        _balances[fondsSouverainReserve] = reserveInitiale;

        totalMznCirculant = circulantInitial;
        totalMznReserveEnAttente = reserveInitiale;

        emit Transfer(address(0), citePcTerrestre, allocPc);
        emit Transfer(address(0), citeGalaxyMobile, allocGalaxy);
        emit Transfer(address(0), fondsSouverainReserve, reserveInitiale);

        // Bloc Genese Synchrone 0
        bytes32 genesisHash = keccak256(abi.encodePacked("GENESIS_AMAL_MIZAN_V6", KERNEL_DT_SCALED, CLE_DOREE_AUTEUR));
        blocsSynchron[0] = BlocSynchronInfo({
            height: 0,
            blocHash: genesisHash,
            prevHash: bytes32(0),
            merkleRootTxs: keccak256(abi.encodePacked("TXS_INITIALES_11M")),
            merkleRootSceaux: keccak256(abi.encodePacked("SCEAU_ORIGINE_A001")),
            timestampUtc: block.timestamp,
            dtScaled: KERNEL_DT_SCALED,
            balancePc: allocPc,
            balanceGalaxy: allocGalaxy,
            balanceQistas: 0,
            wattsLaboScaled: 477000, // 47.7 W
            debitHydroLMin: 313
        });
        dernierBlocHeight = 0;
        emit BlocSynchronScelle(0, genesisHash, block.timestamp);
    }

    // ========================================================================
    //                        FONCTIONS ERC-20 (MZN)
    // ========================================================================

    function totalSupply() external pure override returns (uint256) {
        return TOTAL_SUPPLY;
    }

    function balanceOf(address account) external view override returns (uint256) {
        return _balances[account];
    }

    function transfer(address to, uint256 value) external override returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function allowance(address owner, address spender) external view override returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 value) external override returns (bool) {
        _allowances[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external override returns (bool) {
        uint256 allowed = _allowances[from][msg.sender];
        require(allowed >= value, "Allowance insuffisante");
        if (allowed != type(uint256).max) {
            _allowances[from][msg.sender] = allowed - value;
        }
        _transfer(from, to, value);
        return true;
    }

    function _transfer(address from, address to, uint256 value) internal {
        require(from != address(0), "Transfert depuis adresse zero interdit");
        require(to != address(0), "Transfert vers adresse zero interdit");
        require(_balances[from] >= value, "Solde MZN insuffisant");

        _balances[from] -= value;
        _balances[to] += value;

        emit Transfer(from, to, value);
    }

    // ========================================================================
    //         MODULE FISCAL ETHIQUE : ZAKAT CIVIQUE & SADAQA ZERO-FRICTION
    // ========================================================================

    function transfererSadaqa(address to, uint256 value) external returns (bool) {
        require(to != address(0), "Sadaqa vers adresse zero interdite");
        require(_balances[msg.sender] >= value, "Solde insuffisant pour Sadaqa");

        _balances[msg.sender] -= value;
        _balances[to] += value;

        emit Transfer(msg.sender, to, value);
        emit SadaqaTransferee(msg.sender, to, value);
        return true;
    }

    function preleverZakatSurReserve(address compteAssujetti) external seulementAuteur returns (uint256) {
        uint256 solde = _balances[compteAssujetti];
        require(solde >= NISAB_LOGIQUE_MZN, "Solde inferieur au Nisab");

        uint256 montantZakat = (solde * ZAKAT_BPS) / 10000;
        require(montantZakat > 0, "Montant Zakat nul");

        _balances[compteAssujetti] -= montantZakat;
        _balances[caisseZakatCivique] += montantZakat;

        emit Transfer(compteAssujetti, caisseZakatCivique, montantZakat);
        emit ZakatPrelevee(compteAssujetti, caisseZakatCivique, montantZakat);
        return montantZakat;
    }

    function modifierCaisseZakatCivique(address nouvelleCaisse) external seulementAuteur {
        require(nouvelleCaisse != address(0), "Adresse Caisse invalide");
        caisseZakatCivique = nouvelleCaisse;
    }

    // ========================================================================
    //      CONTRAT COMMERCIAL 50/50 & PARTAGE DES FRUITS SANS USURE
    // ========================================================================

    function verserPartageCommercial5050(address exploitant) external payable {
        require(msg.value > 0, "Montant a partager nul");
        require(exploitant != address(0), "Adresse exploitant invalide");

        uint256 partAuteur = msg.value / 2;
        uint256 partExploitant = msg.value - partAuteur;

        address destinataireAuteur = (TRESORERIE_PRIVEE_AUTEUR != address(0)) ? TRESORERIE_PRIVEE_AUTEUR : CLE_DOREE_AUTEUR;
        (bool ok1, ) = payable(destinataireAuteur).call{value: partAuteur}("");
        require(ok1, "Echec versement part Auteur 50%");

        (bool ok2, ) = payable(exploitant).call{value: partExploitant}("");
        require(ok2, "Echec versement part Exploitant 50%");
    }

    function calculerPartageCommercial5050(uint256 montantTotal) external pure returns (uint256 partAuteur, uint256 partExploitant) {
        partAuteur = montantTotal / 2;
        partExploitant = montantTotal - partAuteur;
    }

    function calculerZakatEligible(address compte) external view returns (uint256 montantZakat, bool estAssujetti) {
        uint256 solde = _balances[compte];
        if (solde >= NISAB_LOGIQUE_MZN) {
            montantZakat = (solde * ZAKAT_BPS) / 10000;
            estAssujetti = true;
        } else {
            montantZakat = 0;
            estAssujetti = false;
        }
    }

    // ========================================================================
    //                     REGISTRE DES ACTES & SCEAUX SCELLES
    // ========================================================================

    function scellerActe(
        address destinataire,
        string calldata codeActe,
        bytes32 sha256Empreinte,
        string calldata description
    ) external returns (uint256) {
        require(destinataire != address(0), "Destinataire invalide");
        require(sha256Empreinte != bytes32(0), "Empreinte SHA-256 nulle interdite");

        uint256 acteId = ++nextActeId;
        registreSceaux[acteId] = SceauActe({
            acteId: acteId,
            codeActe: codeActe,
            sha256Empreinte: sha256Empreinte,
            horodatageUtc: block.timestamp,
            epochKernel: KERNEL_DT_SCALED,
            detenteur: destinataire,
            description: description
        });

        emit ActeScelle(acteId, codeActe, sha256Empreinte, destinataire);
        return acteId;
    }

    // ========================================================================
    //                ENREGISTREMENT DU BLOC SYNCHRON MZN
    // ========================================================================

    function enregistrerBlocSynchron(
        bytes32 blocHash,
        bytes32 prevHash,
        bytes32 merkleRootTxs,
        bytes32 merkleRootSceaux,
        uint256 dtScaled,
        uint256 wattsScaled,
        uint256 debitHydro
    ) external returns (uint256) {
        require(blocHash != bytes32(0), "Hash bloc nul");
        require(prevHash == blocsSynchron[dernierBlocHeight].blocHash, "Hash precedent non concorde");

        uint256 newHeight = dernierBlocHeight + 1;
        blocsSynchron[newHeight] = BlocSynchronInfo({
            height: newHeight,
            blocHash: blocHash,
            prevHash: prevHash,
            merkleRootTxs: merkleRootTxs,
            merkleRootSceaux: merkleRootSceaux,
            timestampUtc: block.timestamp,
            dtScaled: dtScaled,
            balancePc: _balances[citePcTerrestre],
            balanceGalaxy: _balances[citeGalaxyMobile],
            balanceQistas: _balances[citeQistasCivique],
            wattsLaboScaled: wattsScaled,
            debitHydroLMin: debitHydro
        });

        dernierBlocHeight = newHeight;
        emit BlocSynchronScelle(newHeight, blocHash, block.timestamp);
        return newHeight;
    }

    // ========================================================================
    //                  FONCTIONS DE RESOLUTION & EVOLUTION
    // ========================================================================

    function resolveInforme() external pure returns (uint256) {
        return LIGNE_REF_BPS; // 1220 (0.122)
    }

    function resolveForme() external pure returns (uint256) {
        return 5005; // 0.5005 (0.122 + 0.5005 = 0.6225 Mizan)
    }

    function evolve() external {
        emit EvolveContinu(block.number, EPSILON_BPS);
    }

    function purgeKaffara(address from, uint256 amountBps) external {
        require(amountBps <= PLAFOND_BPS, "Depassement plafond");
        uint256 burnAmt = (amountBps * 10**18);
        if (burnAmt > _balances[from]) {
            burnAmt = _balances[from];
        }
        if (burnAmt > 0) {
            _balances[from] -= burnAmt;
            emit KaffaraPurge(from, burnAmt);
        }
    }

    // ========================================================================
    //               STANDARD EIP-2981 : ROYALTIES OFFICIELLES
    // ========================================================================

    uint256 public constant ROYALTY_BPS_DEFAUT = 500; // 5.0% = 500 bps

    function royaltyInfo(uint256 /* tokenId */, uint256 salePrice)
        external
        pure
        override
        returns (address receiver, uint256 royaltyAmount)
    {
        receiver = (TRESORERIE_PRIVEE_AUTEUR != address(0)) ? TRESORERIE_PRIVEE_AUTEUR : CLE_DOREE_AUTEUR;
        royaltyAmount = (salePrice * ROYALTY_BPS_DEFAUT) / 10000;
    }

    function estCompteAuteur(address compte) external pure returns (bool) {
        return (compte == CLE_DOREE_AUTEUR || compte == TRESORERIE_PRIVEE_AUTEUR);
    }

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == 0x01ffc9a7 // ERC-165
            || interfaceId == 0x36372b43 // ERC-20
            || interfaceId == 0x2a5520c3; // ERC-2981 (Royalties)
    }
}
