from iconservice import *

TAG = 'AUTHORIZATION'
DEBUG = False
MULTIPLIER = 1000000000000000000
U_SECONDS_DAY = 86400000000  # Microseconds in a day.


# An interface to get owner of the game's score
class ScoreOwnerInterface(InterfaceScore):
    @interface
    def get_score_owner(self) -> Address:
        pass


class Authorization(IconScoreBase):
    METADATA_FIELDS = ['name', 'scoreAddress', 'minBet', 'maxBet', 'houseEdge',
                       'gameType', 'revShareMetadata', 'revShareWalletAddress',
                       'linkProofPage', 'gameUrlMainnet', 'gameUrlTestnet']
    GAME_TYPE = ['Per wager settlement', 'Game defined interval settlement']
    STATUS_TYPE = ['waiting', 'proposalApproved', 'proposalRejected', 'gameReady',
                   'gameApproved', 'gameRejected', 'gameSuspended', 'gameDeleted']
    _ADMIN_LIST = 'admin_list'
    _SUPER_ADMIN = 'super_admin'
    _PROPOSAL_DATA = 'proposal_data'
    _PROPOSAL_LIST = 'proposal_list'
    _STATUS_DATA = 'status_data'
    _OWNER_DATA = 'owner_data'
    _ROULETTE_SCORE = 'roulette_score'
    _DAY = 'day'
    _PAYOUTS = 'payouts'
    _WAGERS = 'wagers'
    _NEW_DIV_CHANGING_TIME = "new_div_changing_time"
    _GAME_DEVELOPERS_SHARE = "game_developers_share"

    _TODAYS_GAMES_EXCESS = "todays_games_excess"
    # dividends paid according to this excess
    _GAMES_EXCESS_HISTORY = "games_excess_history"

    _APPLY_WATCH_DOG_METHOD = "apply_watch_dog_method"
    _MAXIMUM_PAYOUTS = "maximum_payouts"
    _MAXIMUM_LOSS = "maximum_loss"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        if DEBUG is True:
            Logger.debug(f'In __init__.', TAG)
            Logger.debug(f'owner is {self.owner}.', TAG)
        self._roulette_score = VarDB(self._ROULETTE_SCORE, db, value_type=Address)

        self._admin_list = ArrayDB(self._ADMIN_LIST, db, value_type=Address)
        self._super_admin = VarDB(self._SUPER_ADMIN, db, value_type=Address)
        self._proposal_data = DictDB(self._PROPOSAL_DATA, db, value_type=str)
        self._status_data = DictDB(self._STATUS_DATA, db, value_type=str)
        self._owner_data = DictDB(self._OWNER_DATA, db, value_type=Address)
        self._proposal_list = ArrayDB(self._PROPOSAL_LIST, db, value_type=Address)
        self._day = VarDB(self._DAY, db, value_type=int)
        self._wagers = DictDB(self._WAGERS, db, value_type=int, depth=2)
        self._payouts = DictDB(self._PAYOUTS, db, value_type=int, depth=2)

        self._game_developers_share = VarDB(self._GAME_DEVELOPERS_SHARE, db, value_type=int)
        self._todays_games_excess = DictDB(self._TODAYS_GAMES_EXCESS, db, value_type=int)

        self._new_div_changing_time = VarDB(self._NEW_DIV_CHANGING_TIME, db, value_type=int)
        self._games_excess_history = DictDB(self._GAMES_EXCESS_HISTORY, db, value_type=int, depth=2)

        self._apply_watch_dog_method = VarDB(self._APPLY_WATCH_DOG_METHOD, db, value_type=bool)
        self._maximum_payouts = DictDB(self._MAXIMUM_PAYOUTS, db, value_type=int)
        self._maximum_loss = VarDB(self._MAXIMUM_LOSS, db, value_type=int)

    @eventlog(indexed=2)
    def FundTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @eventlog(indexed=2)
    def ProposalSubmitted(self, sender: Address, scoreAddress: Address):
        pass

    @eventlog(indexed=1)
    def GameSuspended(self, scoreAddress: Address, note: str):
        pass

    def on_install(self) -> None:
        super().on_install()
        self._day.set(self.now() // U_SECONDS_DAY)

    def on_update(self) -> None:
        super().on_update()

    @external
    def untether(self) -> None:
        """
        A function to redefine the value of self.owner once it is possible.
        To be included through an update if it is added to IconService.

        Sets the value of self.owner to the score holding the game treasury.
        """
        if self.tx.origin != self.owner:
            revert(f'Only the owner can call the untether method.')
        pass

    @external
    def set_new_div_changing_time(self, _timestamp: int) -> None:
        """
        Sets the equivalent time of 00:00 UTC of dividend structure changing
        date in microseconds timestamp.
        :param _timestamp: Timestamp of 00:00 UTC of dividend structure changing
                           date in microseconds timestamp
        :type _timestamp: int
        :return:
        """
        if self.msg.sender == self.owner:
            self._new_div_changing_time.set(_timestamp)
            for game in self.get_approved_games():
                self._todays_games_excess.remove(game)

    @external(readonly=True)
    def get_new_div_changing_time(self) -> int:
        """
        Returns the new dividend changing time in microseconds timestamp.
        :return: New dividend changing time in timestamp
        :rtype: int
        """
        return self._new_div_changing_time.get()

    @external
    def set_roulette_score(self, _scoreAddress: Address) -> None:
        """
        Sets the address of roulette/game score
        :param _scoreAddress: Address of roulette
        :type _scoreAddress: :class:`iconservice.base.address.Address`
        :return:
        """
        if self.msg.sender != self.owner:
            revert(f'This function can only be called from the GAS owner.')
        self._roulette_score.set(_scoreAddress)

    @external(readonly=True)
    def get_roulette_score(self) -> Address:
        """
        Returns the roulette score address
        :return: Address of the roulette score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self._roulette_score.get()

    @external
    def set_game_developers_share(self, _share: int) -> None:
        """
        Sets the sum of game developers as well as platform share
        :param _share: Sum of game_devs as well as platform share
        :type _share: int
        :return:
        """
        if self.msg.sender != self.owner:
            revert("This function can only be called by GAS owner")
        self._game_developers_share.set(_share)

    @external(readonly=True)
    def get_game_developers_share(self) -> int:
        """
        Returns the sum of game developers and platform share.
        :return: Sum of game developers share as well as platform share
        :rtype: int
        """
        return self._game_developers_share.get()

    @external
    def set_super_admin(self, _super_admin: Address) -> None:
        """
        Sets super admin. Super admin is also added in admins list. Only allowed
        by the contract owner.
        :param _super_admin: Address of super admin
        :type _super_admin: :class:`iconservice.base.address.Address`
        :return:
        """
        if self.msg.sender == self.owner:
            self._super_admin.set(_super_admin)
            self._admin_list.put(_super_admin)

    @external(readonly=True)
    def get_super_admin(self) -> Address:
        """
        Return the super admin address
        :return: Super admin wallet address
        :rtype: :class:`iconservice.base.address.Address`
        """
        if DEBUG is True:
            Logger.debug(f'{self.msg.sender} is getting super admin address.', TAG)
        return self._super_admin.get()

    @external
    def set_admin(self, _admin: Address) -> None:
        """
        Sets admin. Only allowed by the super admin.
        :param _admin: Wallet address of admin
        :type _admin: :class:`iconservice.base.address.Address`
        :return:
        """
        if self.msg.sender == self._super_admin.get():
            self._admin_list.put(_admin)

    @external(readonly=True)
    def get_admin(self) -> list:
        """
        Returns all the admin list
        :return: List of admins
        :rtype: list
        """
        if DEBUG is True:
            Logger.debug(f'{self.msg.sender} is getting admin addresses.', TAG)
        admin_list = []
        for address in self._admin_list:
            admin_list.append(address)
        return admin_list

    @external
    def remove_admin(self, _admin: Address) -> None:
        """
        Removes admin from the admin arrayDB. Only called by the super admin
        :param _admin: Address of admin to be removed
        :type _admin: :class:`iconservice.base.address.Address`
        :return:
        """
        if self.msg.sender == self.get_super_admin():
            if _admin not in self._admin_list:
                revert('Invalid address: not in list')
            top = self._admin_list.pop()
            if top != _admin:
                for i in range(len(self._admin_list)):
                    if self._admin_list[i] == _admin:
                        self._admin_list[i] = top
            if DEBUG is True:
                Logger.debug(f'{_admin} has been removed from admin list', TAG)

    @payable
    @external
    def submit_game_proposal(self, _gamedata: str) -> None:
        """
        Takes the proposal from new games who want to register in the ICONbet
        platform. The games need to submit game with a fee of 50 ICX as well as
        the game data needs to be a JSON string in the following format:
        {
            "name": ""(Name of the game, str),
            "scoreAddress": "", (User must submit a score address, the game can
                                be completed or else the score can contain the
                                boilerplate score required for ICONbet platform,
                                Address)
            "minBet": , (minBet must be greater than 100000000000000000(0.1 ICX), int)
            "maxBet": , (maxBet in the game in loop, int)
            "houseEdge": "", (house edge of the game in percentage, str)
            "gameType": "", (Type of game, type should be either "Per wager
                            settlement" or "Game defined interval settlement", str)
            "revShareMetadata": "" ,(data about how would you share your revenue)
            "revShareWalletAddress": "", (Wallet address in which you want to
                                         receive your percentage of the excess
                                         made by game)
            "linkProofPage": "" , (link of the page showing the game statistics)
            "gameUrlMainnet": "", (IP of the game in mainnet)
            "gameUrlTestnet": "", (IP of the game in testnet)
        }
        :param _gamedata: JSON object containing the data of game in above format
        :type _gamedata: str
        :return:
        """
        if self.msg.value != 50 * MULTIPLIER:
            revert(f'50 ICX is required for submitting game proposal')
        metadata = json_loads(_gamedata)
        self._check_game_metadata(metadata)
        game_address = Address.from_string(metadata['scoreAddress'])
        score_at_address = self.create_interface_score(game_address, ScoreOwnerInterface)

        if self.msg.sender != score_at_address.get_score_owner():
            revert('Owner not matched')

        self.ProposalSubmitted(self.msg.sender, game_address)
        if game_address in self._proposal_list:
            revert(f'Already listed scoreAddress in the proposal list.')
        self._proposal_list.put(game_address)
        self._owner_data[game_address] = self.msg.sender

        self._status_data[game_address] = 'waiting'
        self._proposal_data[game_address] = _gamedata

        if self._apply_watch_dog_method.get():
            self._maximum_payouts[game_address] = metadata['maxPayout']

    @external
    def set_game_status(self, _status: str, _scoreAddress: Address) -> None:
        """
        Admin can change the game status according to its previous status.
        :param _status: Status of the game.
        :type _status: str
        :param _scoreAddress: Score address of the game for which status is to be changed
        :type _scoreAddress: :class:`iconservice.base.address.Address`
        :return:
        """
        if self.msg.sender not in self.get_admin():
            revert('Sender not an admin')
        if _status not in self.STATUS_TYPE:
            revert('Invalid status')
        gameStatus = self._status_data[_scoreAddress]
        if _status == 'gameRejected' and gameStatus != 'gameReady':
            revert(f'This game cannot be rejected from state {gameStatus}')
        if _status == 'gameApproved' and not (gameStatus == 'gameReady'
                                              or gameStatus == 'gameSuspended'):
            revert(f'This game cannot be approved from state {gameStatus}')
        if _status == 'gameSuspended' and gameStatus != 'gameApproved':
            revert('Only approved games may be suspended.')
        if _status == 'gameDeleted' and gameStatus != 'gameSuspended':
            revert('Only suspended games may be deleted.')

        self._status_data[_scoreAddress] = _status

    @external
    def set_game_ready(self, _scoreAddress: Address) -> None:
        """
        When the game developer has completed the code for SCORE, can set the
        address of the game as ready.
        :param _scoreAddress: Address of the Game which is to be made ready
        :type _scoreAddress: :class:`iconservice.base.address.Address`
        :return:
        """
        if self.msg.sender != self._owner_data[_scoreAddress]:
            revert('Sender not the owner of SCORE ')
        self._status_data[_scoreAddress] = 'gameReady'

    def _check_game_metadata(self, _metadata: dict):
        """
        Sanity checks for the game metadata
        :param _metadata: JSON metadata of the game
        :type _metadata: dict
        :return:
        """
        # All fields should be provided
        for field in self.METADATA_FIELDS:
            if field not in _metadata:
                revert(f'There is no {field} for the game')

        if self._apply_watch_dog_method.get():
            if 'maxPayout' not in _metadata:
                revert(f'There is no maxPayout for the game')

            if _metadata['maxPayout'] < 100000000000000000:  # 0.1 ICX = 10^18 * 0.1
                revert(f"{_metadata['maxPayout']} is less than 0.1 ICX")

        # Check if name is empty
        if _metadata['name'] == '':
            revert('Game name cant be empty')

        # check if scoreAddress is a valid contract address
        if _metadata['scoreAddress'] != '':
            _scoreAddress = Address.from_string(_metadata['scoreAddress'])
            if not _scoreAddress.is_contract:
                revert(f'{_scoreAddress} is not a valid contract address')

        # Check if minbet is within defined limit of 0.1 ICX
        if _metadata['minBet'] < 100000000000000000:  # 0.1 ICX = 10^18 * 0.1
            _minBet = _metadata['minBet']
            revert(f'{_minBet} is less than 0.1 ICX')

        # Check if proper game type is provided
        if _metadata['gameType'] not in self.GAME_TYPE:
            revert('Not a valid game type')

        # Check for revenue share wallet address
        revwallet = _metadata['revShareWalletAddress']
        try:
            revWalletAddress = Address.from_string(revwallet)
            if revWalletAddress.is_contract:
                revert('Not a wallet address')
        except Exception:
            revert('Invalid address while getting game metadata.')

    @external
    def accumulate_daily_wagers(self, game: Address, wager: int) -> None:
        """
        Accumulates daily wagers of the game. Updates the excess of the game.
        Only roulette score can call this function.
        :param game: Address of the game
        :type game: :class:`iconservice.base.address.Address`
        :param wager: Wager amount of the game
        :type wager: int
        :return:
        """
        if self.msg.sender != self._roulette_score.get():
            revert(f'Only roulette score can invoke this method.')
        day = (self.now() // U_SECONDS_DAY)
        self._wagers[day][game] += wager
        if (self._new_div_changing_time.get() is not None
                and self.now() >= self._new_div_changing_time.get()):
            self._todays_games_excess[game] += wager

    @external(readonly=True)
    def get_daily_wagers(self, day: int = 0) -> dict:
        """
        Get daily wagers for a game in a particular day
        :param day: Index of the day for which wagers is to be returned,
                    index=timestamp//(seconds in a day)
        :type day: int
        :return: Wagers for all games on that particular day
        :rtype: dict
        """
        if day < 1:
            day += (self.now() // U_SECONDS_DAY)
        wagers = {}
        for game in self.get_approved_games():
            wagers[str(game)] = f'{self._wagers[day][game]}'
        return wagers

    @external
    def accumulate_daily_payouts(self, game: Address, payout: int) -> bool:
        """
        Accumulates daily payouts of the game. Updates the excess of the game.
        Only roulette score can call this function.
        :param game: Address of the game
        :type game: :class:`iconservice.base.address.Address`
        :param payout: Payout amount of the game
        :type payout: int
        :return:
        """
        if self.msg.sender != self._roulette_score.get():
            revert(f'Only roulette score can invoke this method.')
        day = (self.now() // U_SECONDS_DAY)

        if self._apply_watch_dog_method.get():
            if payout > self._maximum_payouts[game]:
                self._status_data[game] = 'gameSuspended'
                self.GameSuspended(game, f'To prevent overpayment. Requested payout: {payout}. '
                                         f'MaxPayout: {self._maximum_payouts[game]}. {TAG}')
                return False

            if self._payouts[day][game] + payout - self._wagers[day][game] >= self._maximum_loss.get():
                self._status_data[game] = 'gameSuspended'
                self.GameSuspended(game, f'To limit loss. MaxLoss: {self._maximum_loss.get()}. '
                                         f'Loss Incurred if payout: {self._payouts[day][game] + payout - self._wagers[day][game]}, {TAG}')
                return False

        self._payouts[day][game] += payout
        if (self._new_div_changing_time.get() is not None
                and self.now() >= self._new_div_changing_time.get()):
            self._todays_games_excess[game] -= payout
        return True

    @external(readonly=True)
    def get_daily_payouts(self, day: int = 0) -> dict:
        """
        Get daily payouts for a game in a particular day
        :param day: Index of the day for which payouts is to be returned
        :type day: int
        :return: Payouts of the game in that particular day
        :rtype: int
        """
        if day < 1:
            day += (self.now() // U_SECONDS_DAY)
        payouts = {}
        for game in self.get_approved_games():
            payouts[str(game)] = f'{self._payouts[day][game]}'
        return payouts

    @external(readonly=True)
    def get_metadata_fields(self) -> list:
        """
        Returns the metadata fields which the games need to submit while
        submitting proposal.
        :return: List of metadata fields
        :rtype: list
        """
        return self.METADATA_FIELDS

    @external(readonly=True)
    def get_proposal_data(self, _scoreAddress: Address) -> str:
        """
        Returns the proposal data of the game address
        :param _scoreAddress: Game address for which proposal data is to be fetched
        :type _scoreAddress: :class:`iconservice.base.address.Address`
        :return: JSON object of the proposal data of the game
        :rtype: str
        """
        return self._proposal_data[_scoreAddress]

    @external(readonly=True)
    def get_score_list(self) -> list:
        """
        Returns all the games' Address regardless of their status.
        :return: List of games' Address
        :rtype: list
        """
        proposal_list = []
        for scoreAddress in self._proposal_list:
            proposal_list.append(scoreAddress)
        return proposal_list

    @external(readonly=True)
    def get_approved_games(self) -> list:
        """
        Returns all the approved games' Address
        :return: List of approved games
        :rtype: list
        """
        proposal_list = []
        for scoreAddress in self._proposal_list:
            if self._status_data[scoreAddress] == "gameApproved":
                proposal_list.append(scoreAddress)
        return proposal_list

    @external(readonly=True)
    def get_revshare_wallet_address(self, _scoreAddress: Address) -> Address:
        """
        Returns the revshare wallet address of the game
        :param _scoreAddress: Address of the game for which revenue share wallet
                              address is to be fetched
        :type _scoreAddress: :class:`iconservice.base.address.Address`
        :return: Revenue share wallet address of the game
        :rtype: :class:`iconservice.base.address.Address`
        """
        gamedata = self._proposal_data[_scoreAddress]
        metadata = json_loads(gamedata)
        return Address.from_string(metadata['revShareWalletAddress'])

    @external(readonly=True)
    def get_game_type(self) -> list:
        """
        Returns the available types of games.
        :return: List of types of games that the game owner can choose from
        :rtype: list
        """
        return self.GAME_TYPE

    @external(readonly=True)
    def get_game_status(self, _scoreAddress: Address) -> str:
        """
        Returns the status of the game.
        :param _scoreAddress: Address of the game
        :type _scoreAddress: :class:`iconservice.base.address.Address`
        :return: Status of game
        :rtype: str
        """
        return self._status_data[_scoreAddress]

    @external(readonly=True)
    def get_excess(self) -> int:
        """
        Returns the excess share of game developers and founders
        :return: Game developers share
        :rtype: int
        """
        positive_excess: int = 0
        for game in self.get_approved_games():
            game_excess = self._todays_games_excess[game]
            if game_excess >= 0:
                positive_excess += game_excess
        game_developers_amount = (self._game_developers_share.get()
                                  * positive_excess) // 100
        return game_developers_amount

    @external
    def record_excess(self) -> int:
        """
        Roulette score calls this function if the day has been advanced. This
        function takes the snapshot of the excess made by the game till the
        advancement of day.
        :return: Sum of game developers amount
        :rtype: int
        """
        if self.msg.sender != self._roulette_score.get():
            revert("This method can only be called by Roulette score")
        positive_excess: int = 0
        day = (self.now() // U_SECONDS_DAY)
        for game in self.get_approved_games():
            game_excess = self._todays_games_excess[game]
            self._games_excess_history[day - 1][game] = game_excess
            if game_excess >= 0:
                positive_excess += game_excess
                self._todays_games_excess[game] = 0
        game_developers_amount = (self._game_developers_share.get() * positive_excess) // 100
        return game_developers_amount

    @external(readonly=True)
    def get_games_excess(self, day: int = 0) -> dict:
        """
        Returns a dictionary with game addresses as keys and the excess as the
        values for the specified day.
        :return: Dictionary of games' address and excess of the games
        :rtype: dict
        """
        if day == 0:
            return self.get_todays_games_excess()
        if day < 0:
            day += (self.now() // U_SECONDS_DAY)
        games_excess = {}
        for game in self.get_approved_games():
            games_excess[str(game)] = f'{self._games_excess_history[day][game]}'
        return games_excess

    @external(readonly=True)
    def get_yesterdays_games_excess(self) -> dict:
        """
        Returns the dictionary containing keys as games address and value as
        excess of the game of yesterday
        :return: Dictionary of games' address and excess of the games
        :rtype: dict
        """
        return self.get_games_excess(-1)

    @external(readonly=True)
    def get_todays_games_excess(self) -> dict:
        """
        Returns the todays excess of the game. The excess is reset to 0 if it
        remains positive at the end of the day.
        :return: Returns the excess of games at current time
        """
        games_excess = {}
        for game in self.get_approved_games():
            games_excess[str(game)] = f'{self._todays_games_excess[game]}'
        return games_excess

    @payable
    def fallback(self):
        pass

    @external
    def set_maximum_loss(self, maxLoss: int) -> None:
        Logger.debug(f'Setting maxLoss of {maxLoss}')
        if maxLoss < 10 ** 17:  # 0.1 ICX = 10^18 * 0.1
            revert(f'maxLoss is set to a value less than 0.1 ICX')
        if self.msg.sender not in self.get_admin():
            revert('Sender not an admin')
        self._maximum_loss.set(maxLoss)

    @external(readonly=True)
    def get_maximum_loss(self) -> int:
        return self._maximum_loss.get()

    @external
    def set_maximum_payout(self, game: Address, maxPayout: int) -> None:
        if maxPayout < 100000000000000000:  # 0.1 ICX = 10^18 * 0.1
            revert(f'{maxPayout} is less than 0.1 ICX')
        if game not in self._proposal_list:
            revert('Game has not been submitted.')
        if self.msg.sender not in self.get_admin():
            revert('Sender not an admin')

        self._maximum_payouts[game] = maxPayout

    @external(readonly=True)
    def get_maximum_payout(self, game: Address) -> int:
        if game not in self._proposal_list:
            revert('Game has not been submitted.')
        return self._maximum_payouts[game]

    @external
    def toggle_apply_watch_dog_method(self):
        if self.msg.sender not in self.get_admin():
            revert('Sender not an admin')
        old_watch_dog_status = self._apply_watch_dog_method.get()

        if not old_watch_dog_status:
            # All approved games must have minimum_payouts set before applying watch dog methods.
            for scoreAddress in self._proposal_list:
                if self._status_data[scoreAddress] == "gameApproved":
                    if self._maximum_payouts[scoreAddress] < 100000000000000000:
                        revert(f'maxPayout of {scoreAddress} is less than 0.1 ICX')

            if self._maximum_loss.get() < 100000000000000000:
                revert(f'maxLoss is set to a value less than 0.1 ICX')

        self._apply_watch_dog_method.set(
            not self._apply_watch_dog_method.get())

    @external(readonly=True)
    def get_apply_watch_dog_method(self) -> bool:
        return self._apply_watch_dog_method.get()
