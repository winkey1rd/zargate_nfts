from fastapi import APIRouter

wallets_router = APIRouter(prefix="/wallets", tags=["wallets"])

@wallets_router.get("/{address}/optimal-teams")
async def get_wallet_optimal_teams(address: str, basket: bool = False):
    """
    Вернуть оптимальные команды для всех стикеров кошелька, разбитые по skin_tone,
    используя новый алгоритм build_tribe_teams_v2.

    Query parameters:
    - basket: boolean flag; if true, the server will load the current basket from
      the database and apply its owner/recipient rules to the wallet's stickers
      (exclude those the wallet is sending, include incoming ones).
    """
    logging.info(f"get_wallet_optimal_teams called for {address}, basket present={basket}")
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        stickers = sticker_repo.get_by_wallet_address(address)
        if not stickers:
            logging.warning(f"No stickers found for this wallet {address}")
            raise HTTPException(status_code=404, detail="No stickers found for this wallet")

        if basket:
            logging.info(f"Applying basket adjustments for wallet {address}")
            # more efficient: query only relevant rows instead of pulling the entire
            # basket table into memory.
            try:
                repo = BasketRepository(session)
                # items the wallet currently owns and is sending away
                outgoing = repo.filter(owner_address=address)
                # items destined for this wallet
                incoming = repo.filter(recipient_address=address)
                const_exclude = set(it.get('sticker_address') for it in outgoing if it.get('sticker_address'))
                const_addrs = set(it.get('sticker_address') for it in incoming if it.get('sticker_address'))
                if const_exclude:
                    stickers = [s for s in stickers if s.address not in const_exclude]
                for addr in const_addrs:
                    if not any(s.address == addr for s in stickers):
                        s_obj = sticker_repo.get_by_address(addr)
                        if s_obj:
                            stickers.append(s_obj)
            except Exception as e:
                logging.error(f"Error processing basket for wallet {address}: {e}")
                pass

        tribe_builder = TribePowerBuilder(sticker_repo)

        # Группировка по skin_tone
        by_skin = {}
        for s in stickers:
            skin = s.skin_tone or 'Unknown'
            by_skin.setdefault(skin, []).append(s)

        # Для каждого skin_tone — находим все оптимальные команды
        teams = {}
        for skin, skin_stickers in by_skin.items():
            if skin == "Lunar":
                pass
            result = tribe_builder.build_tribe_teams_v2(skin_stickers, team_size=7)
            teams[skin] = [serialize_team(team) for team in result.get("teams", [])]

        # Не формируем секцию ALL для портфолио

        # compute collection synergy info using same logic as wallet stickers endpoint
        try:
            coll = load_collection_json(f"transfer_app/data/{COLLECTION_ADDRESS}.json")
            synergy_conf = coll.get('synergy', {})
            synergy_keywords = set(synergy_conf.get('keywords', []))
            synergy_bonus_table = synergy_conf.get('bonus_table', {})
            synergy_traits = set(synergy_conf.get('traits', []))
        except Exception:
            synergy_keywords = set()
            synergy_bonus_table = {}
            synergy_traits = set()

        return {
            "wallet": address,
            "teams": teams,
            "collection_synergy": {
                "keywords": list(synergy_keywords),
                "bonus_table": synergy_bonus_table,
                "traits": list(synergy_traits)
            }
        }
    finally:
        session.close()
