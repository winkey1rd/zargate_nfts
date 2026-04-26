import sys
sys.path.append("/")

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import os
import json

from backend.app.db import Database
from backend.app.db import WalletRepository, StickerRepository, BasketRepository
from backend.app.models import Sticker, Wallet
from core.old_data_loader import DataLoader
from core.old_synergy_engine import SynergyEngine
from core.old_synergy_initializer import SynergyInitializer
from core.tribe_power_builder import TribePowerBuilder
from old.config import COLLECTION_ADDRESS, SYNERGY_THRESHOLDS, ATTRIBUTE_GROUPS, ATTRIBUTE_EMOJIS
from utils.json_loader import load_collection_json
from core.old_exchange_basket import ExchangeBasket

# Initialize FastAPI
import logging

# configure root logger with file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
root_logger = logging.getLogger()
log_filename = 'basket_api.log'
try:
    if not any(isinstance(h, logging.FileHandler) and os.path.basename(getattr(h, 'baseFilename', '')) == log_filename
                   for h in root_logger.handlers):
        fh = logging.FileHandler(log_filename, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        root_logger.addHandler(fh)
except Exception:
    pass

app = FastAPI(title="NFT Synergy Analyzer", version="1.0.0")

# routers for logical groups
from fastapi import APIRouter

basket_router = APIRouter(prefix="/basket", tags=["basket"])
handbook_router = APIRouter(prefix="/handbook", tags=["handbook"])
wallets_router = APIRouter(prefix="/wallets", tags=["wallets"])
stickers_router = APIRouter(prefix="/stickers", tags=["stickers"])

# include routers at bottom of file (after definitions)

logging.info("API module imported, server initializing")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
db = Database("transfer_app/transfer_app/data/stickers.db")
data_loader = DataLoader(db)
basket = ExchangeBasket()

# ==================== HELPER FUNCTIONS ====================
def serialize_sticker_full(s):
    """Сериализация стикера со всеми полями для портфолио и API"""
    if s is None:
        return None
    
    # Получить синергии стикера и добавить эмодзи
    synergies_list = []
    if hasattr(s, 'get_synergies'):
        raw_synergies = s.get_synergies()
        print(f"[serialize_sticker_full] Sticker {s.address}: has get_synergies, got {len(raw_synergies)} synergies: {raw_synergies}")
        for synergy in raw_synergies:
            emoji = ATTRIBUTE_EMOJIS.get(synergy.get('group_name'), '✨')
            synergies_list.append({
                "emoji": emoji,
                "group_name": synergy.get('group_name'),
                "attr_value": synergy.get('attr_value'),
                "max_row_count": synergy.get('max_row_count')
            })
    else:
        print(f"[serialize_sticker_full] Sticker {s.address}: NO get_synergies method")
    
    return {
        "id": getattr(s, 'id', None),
        "address": getattr(s, 'address', None),
        "name": getattr(s, 'name', None),
        "image_url": getattr(s, 'image_url', None),
        "wallet_address": (s.wallet.address if getattr(s, 'wallet', None) else None),
        "score": getattr(s, 'total_value', 0),
        "attr_value": getattr(s, 'attr_value', 0),
        "synergy_bonus": getattr(s, 'synergy_bonus', 0),
        "name_value": getattr(s, 'name_value', 0),
        "attributes": s.get_attributes() if hasattr(s, 'get_attributes') else {},
        "emotion": getattr(s, 'emotion', None),
        "skin_tone": getattr(s, 'skin_tone', None),
        "synergies": synergies_list
    }

def serialize_team(team_stickers):
    """Сериализация команды (список стикеров или dict эмоция->стикер) с метаданными"""
    if isinstance(team_stickers, dict):
        team_stickers = list(team_stickers.values())
    # Извлечь уникальные эмоции из команды
    emotions = list(set(getattr(s, 'emotion', 'NEUTRAL') for s in team_stickers if getattr(s, 'emotion', None)))
    is_complete = len(team_stickers) == 7
    
    return {
        "stickers": [serialize_sticker_full(s) for s in team_stickers],
        "emotions": emotions,
        "is_complete": is_complete,
        "total_pwr": sum(getattr(s, 'total_value', 0) for s in team_stickers)
    }

# ==================== PORTFOLIO OPTIMAL TEAMS ENDPOINT ====================
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

# ==================== WALLET OPTIMAL TRIBE TEAMS V2 ENDPOINT ====================
@wallets_router.get("/{address}/optimal-tribe-teams-v2")
async def get_wallet_optimal_tribe_teams_v2(address: str, basket: bool = False):
    """
    Вернуть оптимальные команды для всех стикеров кошелька, разбитые по skin_tone,
    используя новый алгоритм build_tribe_teams_v2.

    Query parameters:
    - basket: boolean flag; if true, the server will load the current basket from
      the database and apply its owner/recipient rules to the wallet's stickers
      (exclude those the wallet is sending, include incoming ones).
    """
    logging.info(f"get_wallet_optimal_tribe_teams_v2 called for {address}, basket present={basket}")
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
            if skin == "Demonic":
                pass
            result = tribe_builder.build_tribe_teams_v2(skin_stickers, team_size=7)
            # Сериализуем все найденные команды
            teams[skin] = [serialize_team(team) for team in result["teams"]]

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

# ==================== OPTIMAL TEAM ENDPOINT ====================
@app.get("/optimal-team")
async def get_optimal_team(
    skin_tone: Optional[str] = None,
    team_size: int = 7
):
    """Get optimal teams of stickers maximizing PWR and synergy overlap."""
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        synergy_engine = SynergyEngine(sticker_repo)

        # Get stickers: filter by skin_tone if provided, otherwise all
        if skin_tone:
            stickers = session.query(Sticker).filter(Sticker.skin_tone == skin_tone).all()
        else:
            stickers = session.query(Sticker).all()
        if not stickers:
            raise HTTPException(status_code=400, detail="No stickers found for selection")

        teams_list = synergy_engine.build_optimal_team(stickers, team_size=team_size)
        return {
            "teams": [serialize_team(team) for team in teams_list],
            "total_teams": len(teams_list),
            "skin_tone": skin_tone or "ALL"
        }
    finally:
        session.close()


# ==================== TRIBE POWER MAXIMIZATION ENDPOINT ====================
@app.get("/optimal-tribe-teams")
async def get_optimal_tribe_teams(
    skin_tone: Optional[str] = None,
    team_size: int = 7
):
    """
    Get optimal teams using Tribe Power Maximization algorithm.
    
    This algorithm differs from /optimal-team:
    - Maximizes TOTAL power of all teams (tribe), not individual teams
    - Resolves synergy conflicts globally for best overall result
    - May provide different team compositions but higher total power
    
    Query parameters:
    - skin_tone: Filter by skin tone (optional, default: ALL)
    - team_size: Target team size (default: 7)
    """
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        tribe_builder = TribePowerBuilder(sticker_repo)

        # Get stickers: filter by skin_tone if provided, otherwise all
        if skin_tone:
            stickers = session.query(Sticker).filter(Sticker.skin_tone == skin_tone).all()
        else:
            stickers = session.query(Sticker).all()
        
        if not stickers:
            raise HTTPException(status_code=400, detail="No stickers found for selection")

        result = tribe_builder.build_optimal_tribe_teams(stickers, team_size=team_size)
        
        return {
            "teams": [serialize_team(team) for team in result["teams"]],
            "total_teams": len(result["teams"]),
            "total_tribe_power": result["total_power"],
            "skin_tone": skin_tone or "ALL",
            "synergy_summary": {
                "activated_count": len(result["synergy_summary"]["activated"]),
                "failed_count": len(result["synergy_summary"]["failed"]),
                "conflicts_resolved_count": len(result["synergy_summary"]["conflicts_resolved"])
            },
            "decision_log": result["decision_log"] if result["decision_log"] else None
        }
    finally:
        session.close()


@app.get("/compare-algorithms")
async def compare_algorithms_endpoint(
    skin_tone: Optional[str] = None,
    team_size: int = 7
):
    """
    Compare old (build_optimal_team) vs new (TribePowerBuilder) algorithms.
    
    Returns both results side-by-side for A/B testing and validation.
    """
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        
        # Get stickers
        if skin_tone:
            stickers = session.query(Sticker).filter(Sticker.skin_tone == skin_tone).all()
        else:
            stickers = session.query(Sticker).all()
        
        if not stickers:
            raise HTTPException(status_code=400, detail="No stickers found for selection")
        
        # OLD ALGORITHM
        synergy_engine = SynergyEngine(sticker_repo)
        old_teams = synergy_engine.build_optimal_team(stickers, team_size=team_size)
        old_power = sum(
            sum(s.total_value for s in team) + (350 if len(team) >= team_size else 0)
            for team in old_teams
        )
        
        # NEW ALGORITHM
        tribe_builder = TribePowerBuilder(sticker_repo)
        new_result = tribe_builder.build_optimal_tribe_teams(stickers, team_size=team_size)
        new_power = new_result["total_power"]
        
        # Calculate improvement
        power_gain = new_power - old_power
        power_gain_percent = (power_gain / old_power * 100) if old_power > 0 else 0
        
        return {
            "old_algorithm": {
                "name": "build_optimal_team (Iterative Greedy)",
                "total_power": old_power,
                "num_teams": len(old_teams),
                "teams": [serialize_team(team) for team in old_teams]
            },
            "new_algorithm": {
                "name": "TribePowerBuilder (Global Optimization)",
                "total_power": new_power,
                "num_teams": len(new_result["teams"]),
                "teams": [serialize_team(team) for team in new_result["teams"]],
                "synergies_activated": len(new_result["synergy_summary"]["activated"])
            },
            "comparison": {
                "power_gain": power_gain,
                "power_gain_percent": power_gain_percent,
                "recommendation": "NEW" if power_gain_percent > 5 else ("NEW (slight)" if power_gain_percent > 0 else "EQUIVALENT")
            }
        }
    finally:
        session.close()


# ==================== SYNERGY INITIALIZATION ====================
@app.post("/initialize-synergies")
async def initialize_synergies():
    """
    Initialize synergies for all stickers.
    
    This endpoint scans all stickers, finds synergies (4+ elements per attribute group),
    and assigns synergy information to participating stickers.
    
    Should be called after loading wallets or when sticker data changes.
    """
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        initializer = SynergyInitializer(sticker_repo)
        
        result = initializer.initialize_all_synergies()
        
        return {
            "status": "success",
            "message": f"Initialized {result['total_synergies_found']} synergies for {result['total_stickers_with_synergies']} stickers",
            "details": result
        }
    except Exception as e:
        logging.error(f"Error initializing synergies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.delete("/clear-synergies")
async def clear_synergies():
    """Clear all synergy assignments from stickers."""
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        initializer = SynergyInitializer(sticker_repo)
        
        count = initializer.clear_all_synergies()
        
        return {
            "status": "success",
            "message": f"Cleared synergies from {count} stickers"
        }
    except Exception as e:
        logging.error(f"Error clearing synergies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ==================== DATABASE MANAGEMENT ====================
@wallets_router.get("")
async def get_wallets():
    """Получить все кошельки из БД"""
    session = db.get_session()
    try:
        wallet_repo = WalletRepository(session)
        wallets = wallet_repo.get_all()
        return {
            "wallets": [
                {
                    "address": w.address,
                    "total_stickers": w.total_stickers,
                    # `Wallet` model may use `created_at` or `last_updated`; fall back safely
                    "loaded_at": (
                        getattr(w, 'created_at', None) or getattr(w, 'last_updated', None)
                    ).isoformat() if (getattr(w, 'created_at', None) or getattr(w, 'last_updated', None)) else None
                }
                for w in wallets
            ]
        }
    finally:
        session.close()


# ==================== BASKET STORAGE ENDPOINTS ====================

@basket_router.get("/stickers")
async def get_basket_stickers():
    """Return full sticker info for every item currently in the basket.

    The response is a list of dictionaries matching the frontend format with synergies included.
    """
    session = db.get_session()
    try:
        repo = BasketRepository(session)
        items = repo.get_all()
        # enrich with sticker metadata if available
        sticker_repo = StickerRepository(session)
        result = []
        for it in items:
            st = sticker_repo.get_by_address(it['sticker_address'])
            if st:
                # Use serialize_sticker_full to get synergies and all fields
                sticker_data = serialize_sticker_full(st)
                # Add basket-specific fields
                sticker_data['owner'] = it['owner_address'] or ''
                sticker_data['recipient'] = it['recipient_address'] or ''
                print(f"[get_basket_stickers] Sticker {st.address}: synergies={sticker_data.get('synergies', [])}")
                result.append(sticker_data)
            else:
                # Fallback if sticker not found in DB
                result.append({
                    'address': it['sticker_address'],
                    'name': it['sticker_address'],
                    'image_url': '',
                    'skin_tone': '',
                    'emotion': '',
                    'score': 0,
                    'owner': it['owner_address'] or '',
                    'recipient': it['recipient_address'] or '',
                    'synergies': []
                })
        print(f"[get_basket_stickers] Returning {len(result)} stickers with synergies")
        return result
    finally:
        session.close()

@basket_router.post("/sticker/add")
async def add_basket_sticker(payload: Dict):
    """Add a single sticker to the basket.

    Payload must include `sticker_address`, `owner` and `recipient`.
    """
    addr = payload.get('sticker_address')
    owner = payload.get('owner')
    recipient = payload.get('recipient')
    if not addr:
        raise HTTPException(status_code=400, detail="sticker_address required")
    session = db.get_session()
    try:
        repo = BasketRepository(session)
        created = repo.add_item(sticker_address=addr, owner_address=owner, recipient_address=recipient)
        return created
    finally:
        session.close()

@basket_router.post("/sticker/update")
async def update_basket_sticker(payload: Dict):
    """Update recipient for a sticker already in the basket."""
    addr = payload.get('sticker_address')
    recipient = payload.get('recipient')
    if not addr:
        raise HTTPException(status_code=400, detail="sticker_address required")
    session = db.get_session()
    try:
        repo = BasketRepository(session)
        updated = repo.update_item(sticker_address=addr, recipient_address=recipient)
        if not updated:
            raise HTTPException(status_code=404, detail="Sticker not found in basket")
        return updated
    finally:
        session.close()

@basket_router.post("/sticker/delete")
async def delete_basket_sticker(payload: Dict):
    """Remove a sticker from the basket by address."""
    addr = payload.get('sticker_address')
    if not addr:
        raise HTTPException(status_code=400, detail="sticker_address required")
    session = db.get_session()
    try:
        repo = BasketRepository(session)
        success = repo.delete_item(sticker_address=addr)
        if not success:
            raise HTTPException(status_code=404, detail="Sticker not found in basket")
        return {"status": "deleted"}
    finally:
        session.close()

@basket_router.post("/clear")
async def clear_basket():
    """Delete all records from basket."""
    session = db.get_session()
    try:
        repo = BasketRepository(session)
        repo.clear_all()
        return {"status": "cleared"}
    finally:
        session.close()

# previously-existing generic /api/baskets endpoints were removed in favour of the
# more granular routes above.  They were not being used by the frontend anymore.

@app.post("/load-wallets")
async def load_wallets(wallets: List[str]):
    """Загрузить NFT для кошельков в БД"""
    results = []
    total = len(wallets)
    
    for idx, wallet in enumerate(wallets):
        wallet = wallet.strip()
        if not wallet:
            continue
            
        try:
            await data_loader.load_wallet(wallet, COLLECTION_ADDRESS)
            results.append({
                "wallet": wallet,
                "status": "success",
                "progress": (idx + 1) / total
            })
        except Exception as e:
            results.append({
                "wallet": wallet,
                "status": "error",
                "error": str(e),
                "progress": (idx + 1) / total
            })
    
    return {"results": results}

@app.delete("/database")
async def clear_database():
    """Очистить базу данных"""
    session = db.get_session()
    try:
        session.query(Sticker).delete()
        session.query(Wallet).delete()
        session.commit()
        return {"status": "cleared"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

# ==================== SYNERGY ANALYSIS ====================
@stickers_router.get("/skins")
async def get_skins():
    """Получить все доступные skin tones"""
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        all_stickers = sticker_repo.session.query(Sticker).all()
        all_skins = sorted(set(s.skin_tone for s in all_stickers if s.skin_tone))

        if not all_skins:
            raise HTTPException(status_code=400, detail="No skins found in database")

        # Try to order by rarity from collection JSON
        try:
            coll = load_collection_json(f"transfer_app/data/{COLLECTION_ADDRESS}.json")
            skin_map = coll.get('attribute', {}).get('Skin Tone', {})
            skins_ordered = sorted(skin_map.keys(), key=lambda k: skin_map.get(k, 0), reverse=True)
            skins_to_show = [s for s in skins_ordered if s in all_skins] + [s for s in all_skins if s not in skins_ordered]
        except Exception:
            skins_to_show = all_skins

        return {"skins": skins_to_show}
    finally:
        session.close()

# handbook synonyms -----------------------------------------------------------
@handbook_router.get("/wallets")
async def handbook_wallets():
    return await get_wallets()

@handbook_router.get("/skins")
async def handbook_skins():
    return await get_skins()

@handbook_router.get("/attribute-groups")
async def handbook_attr_groups():
    return await get_attribute_groups()

@handbook_router.get("/emotions")
async def handbook_emotions():
    """Return the set of emotion names currently present in the stickers table."""
    session = db.get_session()
    try:
        emotions = session.query(Sticker.emotion).distinct().all()
        emotions_list = [e[0] for e in emotions if e[0]]
        return {"emotions": sorted(emotions_list)}
    finally:
        session.close()

@stickers_router.get("/attribute-groups")
async def get_attribute_groups():
    """Получить доступные группы атрибутов"""
    return {"groups": list(ATTRIBUTE_GROUPS.keys())}

@stickers_router.get("/synergies")
async def get_synergies(
    skin_tone: Optional[str] = None,
    attribute_group: Optional[str] = None,
    wallet_priority: Optional[str] = None
):
    """Получить синергии для выбранного skin tone и/или attribute group.
    Если оба None, показывает все данные.

    Метод прежде работал по кэшу: таблица `synergies` содержала уже
    рассчитанные строки, поэтому реализация ниже сначала пытается
    прочитать данные из таблицы и вернуть их напрямую.  Это является
    «старым методом формирования синергий», который пользователь просил
    вернуть.  Если таблица отсутствует или пуста – падаем обратно на
    динамический расчёт через SynergyEngine.
    """
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        synergy_engine = SynergyEngine(sticker_repo)
        wallet_repo = WalletRepository(session)

        # attempt to use cached synergies table if present
        try:
            has_table = session.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='synergies';"
            ).fetchone()
            if has_table:
                rows = session.execute(
                    "SELECT wallet, skin_tone, group_name, value, sticker_addresses FROM synergies"
                ).fetchall()
                if rows:
                    # build structure similar to old output
                    serializable = {}
                    for wallet, skin, group, val, addrs_json in rows:
                        if skin_tone and skin != skin_tone:
                            continue
                        if attribute_group and group != attribute_group:
                            continue
                        try:
                            addrs = json.loads(addrs_json or '[]')
                        except Exception:
                            addrs = []
                        stickers = []
                        for addr in addrs:
                            s = sticker_repo.get_by_address(addr)
                            if s:
                                stickers.append(serialize_sticker_full(s))

                        if val not in serializable:
                            serializable[val] = {
                                'total_count': 0,
                                'max_row_count': 0,
                                'rows': [],
                                # skin and group stored in cache may be generic ("ALL");
                                # override them below if a specific filter was used.
                                'skin_tone': skin,
                                'attribute_group': group,
                                # cache doesn't include alternates but UI expects key
                                'alternatives': []
                            }
                        entry = serializable[val]
                        # ensure metadata preserved; prefer the requested filter values
                        entry['skin_tone'] = skin_tone or skin or 'ALL'
                        entry['attribute_group'] = attribute_group or group or 'ALL'
                        entry['rows'].append([{'wallet_address': wallet, 'stickers': stickers}])
                        entry['total_count'] += len(stickers)
                        entry['max_row_count'] = max(entry['max_row_count'], len(stickers))

                    # If we applied filters but the cache entries all still carry "ALL"
                    # metadata, it's a sign the cache was populated without distinctions.
                    if (skin_tone and any(v.get('skin_tone') == 'ALL' for v in serializable.values())):
                        print(f"[WARN] returning cached synergies for skin_tone={skin_tone} but metadata still 'ALL'")
                    if (attribute_group and any(v.get('attribute_group') == 'ALL' for v in serializable.values())):
                        print(f"[WARN] returning cached synergies for attribute_group={attribute_group} but metadata still 'ALL'")

                    # Only return cached results if we have matching data; otherwise fall back to dynamic calculation
                    if serializable:
                        return {
                            "skin_tone": skin_tone or "ALL",
                            "attribute_group": attribute_group or "ALL",
                            "total_unique": len(serializable),
                            "synergies": serializable
                        }
        except Exception as _:
            # If cache read fails, fall back to dynamic calculation
            pass

        # Get wallets for reference
        wallets_in_db = wallet_repo.get_all()
        all_wallets = [w.address for w in wallets_in_db]

        # We used to filter and regroup stickers here manually, but the engine already
        # provides build_synergies() which encapsulates all of that logic and is
        # verified to produce correct results.  Call it for each attribute group we
        # care about instead of duplicating internal helpers.

        # Determine groups we need to process.
        if attribute_group:
            groups_to_process = [attribute_group]
        else:
            groups_to_process = list(ATTRIBUTE_GROUPS.keys())

        computed_by_group = {}
        for group_name in groups_to_process:
            try:
                if group_name in ('PAIRS', 'TRIPLES'):
                    logging.info(f"Building multi-synergies for {group_name}")
                    sy_map = synergy_engine.build_multi_synergies(group_name, skin_tone or None, wallet_priority)
                    logging.info(f"Built {len(sy_map)} multi-synergies for {group_name}")
                else:
                    sy_map = synergy_engine.build_synergies(group_name, skin_tone or None, wallet_priority)
            except Exception as e:
                logging.error(f"build synergies failed for group {group_name}: {e}")
                sy_map = {}
            if sy_map:
                computed_by_group[group_name] = sy_map

        # Convert internal sticker objects into serializable sticker-card dicts
        serialize_sticker = serialize_sticker_full

        def transform_synergy_data(sy_data, group_name):
            # Transform internal synergy rows into list-of-objects, one object per row.
            # We no longer deduplicate by sticker set; duplicates (same emotion appearing
            # in multiple rows) must be preserved so the client can render them on
            # separate lines. Each row object carries its own wallet groups and an
            # explicit list of emotions present.
            threshold = SYNERGY_THRESHOLDS.get(group_name, 0)
            rows_out = []

            for row in sy_data.get('rows', []):
                emotions = row.get('emotions', {})
                # wallet_groups: wallet_address -> list of sticker entries
                wallet_groups = {}
                row_emotions = []

                for emotion, info in emotions.items():
                    row_emotions.append(emotion)
                    wallets_map = info.get('wallets', {})
                    count = info.get('count', 0)
                    for wallet_addr, sticker_obj in wallets_map.items():
                        sticker_serial = serialize_sticker(sticker_obj)
                        if not sticker_serial:
                            continue

                        if count >= threshold and threshold > 0:
                            synergy_level = 'synergy'
                        elif count > 0:
                            synergy_level = 'partial'
                        else:
                            synergy_level = 'none'

                        entry = {
                            'sticker': sticker_serial,
                            'emotion': emotion,
                            'count': count,
                            'synergy_level': synergy_level,
                            'attr_value': getattr(sticker_obj, 'attr_value', 0),
                            'synergy_bonus': getattr(sticker_obj, 'synergy_bonus', 0),
                            'name_value': getattr(sticker_obj, 'name_value', 0)
                        }

                        wallet_groups.setdefault(wallet_addr or 'unknown', []).append(entry)

                # Order wallets by their highest sticker score descending
                wallet_order = sorted(wallet_groups.keys(), key=lambda w: -max((e['sticker'].get('score') or 0) for e in wallet_groups[w]))

                row_wallets = []
                for w in wallet_order:
                    items = wallet_groups[w]
                    stickers_list = [it['sticker'] for it in items]
                    meta_list = [{'emotion': it['emotion'], 'count': it['count'], 'synergy_level': it['synergy_level'], 'attr_value': it.get('attr_value', 0), 'synergy_value': it.get('synergy_bonus', 0), 'name_value': it.get('name_value', 0)} for it in items]
                    row_wallets.append({'wallet_address': w, 'stickers': stickers_list, 'meta': meta_list})

                # preserve attribute count from engine if provided
                row_entry = {'wallet_groups': row_wallets, 'emotions': row_emotions}
                if 'row_attr_count' in row:
                    row_entry['row_attr_count'] = row.get('row_attr_count')
                rows_out.append(row_entry)

            out = {
                'total_count': sy_data.get('total_count', 0),
                'max_row_count': sy_data.get('max_row_count', 0),
                'rows': rows_out,
                'remaining': sy_data.get('remaining', 0)
            }
            # include alternative/remaining sticker list if engine supplied it
            if sy_data.get('remaining_items'):
                out['alternatives'] = [serialize_sticker(s) for s in sy_data.get('remaining_items', [])]
            else:
                out['alternatives'] = []
            return out

        # Sort by max_row_count
        computed = {}
        for group_name in groups_to_process:
            if group_name not in computed_by_group:
                continue
            for attr_value, sy_data in computed_by_group[group_name].items():
                computed[attr_value] = sy_data

        sorted_results = dict(sorted(
            computed.items(),
            key=lambda x: x[1].get('max_row_count', 0),
            reverse=True
        ))

        # Transform results into serializable form
        serializable = {}
        for attr_value, sy_data in sorted_results.items():
            # Determine which group this attribute belongs to
            sy_group = attribute_group  # Use provided group, or infer from computed data
            for gname in groups_to_process:
                if gname in computed_by_group and attr_value in computed_by_group[gname]:
                    sy_group = gname
                    break
            entry = transform_synergy_data(sy_data, sy_group)
            # attach metadata so frontend can filter correctly
            entry['attribute_group'] = sy_group or 'ALL'
            entry['skin_tone'] = skin_tone or 'ALL'
            serializable[attr_value] = entry

        return {
            "skin_tone": skin_tone or "ALL",
            "attribute_group": attribute_group or "ALL",
            "total_unique": len(serializable),
            "synergies": serializable
        }
    finally:
        session.close()

# Note: legacy in-memory basket management endpoints were removed; clients now use
# /basket/... routes that interact with the database via BasketRepository.


@wallets_router.get("/{address}/stickers")
async def get_wallet_stickers(address: str, basket: bool = False):
    """Return stickers for a given wallet.

    If `basket` is true, the server will load the current basket from the
    database and apply its owner/recipient rules to modify the response
    (exclude items the wallet is sending and include incoming ones).
    """
    session = db.get_session()
    try:
        sticker_repo = StickerRepository(session)
        stickers = sticker_repo.get_by_wallet_address(address)

        if basket:
            repo = BasketRepository(session)
            items = repo.get_all()
            exclude_set = set()
            additions_addrs = set()
            for it in items:
                addr = it.get('sticker_address')
                owner = it.get('owner_address')
                recip = it.get('recipient_address')
                if owner == address and addr:
                    exclude_set.add(addr)
                if recip == address and addr:
                    additions_addrs.add(addr)
            if exclude_set:
                stickers = [s for s in stickers if s.address not in exclude_set]
            for addr in additions_addrs:
                if not any(s.address == addr for s in stickers):
                    s_obj = sticker_repo.get_by_address(addr)
                    if s_obj:
                        stickers.append(s_obj)

        # Load collection synergy config
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

        def extract_themes_from_attrs(attrs: dict):
            themes = []
            for grp, vals in attrs.items():
                if isinstance(vals, str):
                    vals = [vals]
                for v in vals:
                    if not v:
                        continue
                    for word in str(v).split():
                        if word in synergy_keywords:
                            themes.append(word)
            return themes

        def serialize(s):
            attrs = s.get_attributes() if hasattr(s, 'get_attributes') else {}
            themes = extract_themes_from_attrs(attrs)
            return {
                "address": s.address,
                "name": s.name,
                "image_url": s.image_url,
                "emotion": s.emotion,
                "skin_tone": s.skin_tone,
                "score": getattr(s, 'total_value', 0) or 0,
                "attr_value": getattr(s, 'attr_value', 0) or 0,
                "synergy_bonus": getattr(s, 'synergy_bonus', 0) or 0,
                "name_value": getattr(s, 'name_value', 0) or 0,
                "attributes": attrs,
                "themes": themes,
            }

        return {
            "wallet": address,
            "stickers": [serialize(s) for s in stickers],
            "collection_synergy": {
                "keywords": list(synergy_keywords),
                "bonus_table": synergy_bonus_table,
                "traits": list(synergy_traits)
            }
        }
    finally:
        session.close()


@stickers_router.get("/{address}")
async def get_sticker(address: str):
    """Get a single sticker by its address."""
    session = db.get_session()
    try:
        sticker = session.query(Sticker).filter(Sticker.address == address).first()
        if not sticker:
            raise HTTPException(status_code=404, detail="Sticker not found")
        return serialize_sticker_full(sticker)
    finally:
        session.close()

# ==================== STATIC FILES ====================
# Serve HTML files (use absolute paths based on this module)
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

# mount routers FIRST before any catch-all handlers
app.include_router(basket_router)
app.include_router(handbook_router)
app.include_router(wallets_router)
app.include_router(stickers_router)

# Mount static files at /static for direct access
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def get_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index file not found")

@app.get("/{path:path}")
async def get_static(path: str):
    # avoid serving index.html for API calls that aren't matched by routers
    if path.startswith("stickers/") or path.startswith("wallets/") or path.startswith("basket/") or path.startswith("handbook/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
