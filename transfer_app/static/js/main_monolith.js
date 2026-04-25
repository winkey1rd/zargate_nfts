// ===============================
// SECTION: legacy basket logic (from app.js)
// ===============================
/**
 * Legacy basket logic restored from app.js
 * Includes addToBasket, removeFromBasket, toggleBasket, showRecipientMenu, renderBasketGroup, updateExchangeBaskets, and helpers
 */
// ...legacy basket logic code...
// ...existing code...
// Новый монолит main.js
// Перенесён код из текущей реализации (main.js)

/**
 * main.js — Application entry point (ES6 modules)
 * 
 * Перенос из текущего main.js
 */

// [Imports removed for monolith]

console.log('=== Application Starting ===');

// --- Begin state.js ---
// State management functions (originally from modules/state.js)
function createAppState() {
  return {
    selectedSkin: null,
    selectedGroup: null,
    selectedPortfolioSkin: null,
    walletsInDb: [],
    currentSynergies: null,
    basket: new Map(),
    skinsList: []
  };
}
function createExchangeState() {
  return {
    wallets: [],
    pool: []
  };
}
function createPortfolioState() {
  return {
    lastStickerResults: [],
    currentWalletIndex: 0,
    adjustments: {}
  };
}
// --- End state.js ---

// ===============================
// SECTION: ui.js (moved here for early use)
// ===============================
// UI initialization, event handling, DOM manipulation
var ui = {};
ui.initDOMElements = function() {
  return {
    walletsInput: document.getElementById('wallets-input'),
    loadBtn: document.getElementById('load-btn'),
    clearBtn: document.getElementById('clear-btn'),
    progressContainer: document.getElementById('progress-container'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    statistics: document.getElementById('statistics'),
    totalStickers: document.getElementById('total-stickers'),
    totalWallets: document.getElementById('total-wallets'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    portfolioTab: document.getElementById('portfolio'),
    synergyTab: document.getElementById('synergies'),
    basketTab: document.getElementById('basket'),
    portfolioSection: document.getElementById('portfolio-content'),
    walletSelector: document.getElementById('wallet-selector'),
    portfolioStats: document.getElementById('portfolio-stats'),
    loadingMessage: document.getElementById('loading-message'),
    synergyContent: document.getElementById('synergy-content'),
    skinsContainer: document.getElementById('skins-container'),
    groupsContainer: document.getElementById('groups-container'),
    synergyFilterContainer: document.getElementById('synergy-filters'),
    synergyStats: document.getElementById('synergy-stats'),
    selectionMessage: document.getElementById('selection-message'),
    synergyResults: document.getElementById('synergy-results'),
    resultsHeader: document.getElementById('results-header'),
    synergySection: document.getElementById('synergy-list'),
    basketEmpty: document.getElementById('basket-empty'),
    basketContent: document.getElementById('basket-content'),
    basketItems: document.getElementById('basket-items'),
    basketImportBtn: document.getElementById('basket-import-input'),
    basketClearBtn: document.getElementById('basket-clear-btn'),
    basketExportBtn: document.getElementById('basket-export-btn')
  };
};
ui.setupEventListeners = function(appState, exchangeState, portfolioState, domElements) {
  console.log('setupEventListeners called');
  domElements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      ui.switchTab(btn.dataset.tab, appState, exchangeState, portfolioState, domElements);
    });
  });
  if (domElements.loadBtn) {
    domElements.loadBtn.addEventListener('click', () => {
      console.log('Load button clicked');
      ui.loadWallets(appState, domElements);
    });
  }
  if (domElements.clearBtn) {
    domElements.clearBtn.addEventListener('click', () => {
      console.log('Clear button clicked');
      ui.clearDatabase(appState, domElements);
    });
  }
  if (domElements.basketClearBtn) {
    domElements.basketClearBtn.addEventListener('click', async () => {
      if (!confirm('Clear all items from basket?')) return;
      try {
        await apiClearBasket();
      } catch (err) {
        console.warn('clear basket API error', err);
      }
      appState.basket.clear();
      portfolioState.adjustments = {};
      exchangeState.wallets = [];
      exchangeState.pool = [];
      document.querySelectorAll('.basket-btn').forEach(btn => {
        btn.textContent = '+';
        btn.classList.remove('active');
      });
      if (domElements.onBasketUpdated) domElements.onBasketUpdated();
      if (domElements.updatePortfolioIfActive) domElements.updatePortfolioIfActive();
    });
  }
  if (domElements.basketExportBtn) {
    domElements.basketExportBtn.addEventListener('click', async () => {
      try {
        const resp = await fetch(`${API_URL}/basket/stickers`);
        if (!resp.ok) throw new Error('export failed');
        const items = await resp.json();
        const json = JSON.stringify(items, null, 2);
        const dataUrl = 'data:application/json;charset=utf-8,' + encodeURIComponent(json);
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = 'basket_' + new Date().toISOString().split('T')[0] + '.json';
        link.click();
      } catch (err) {
        ui.showMessage('Failed to export basket: ' + err.message, 'error');
      }
    });
  }
  if (domElements.basketImportBtn) {
    domElements.basketImportBtn.addEventListener('change', async (event) => {
      var file = event.target.files[0];
      if (!file) return;
      try {
        var text = await file.text();
        var items = JSON.parse(text);
        // clear existing state
        appState.basket.clear();
        // for each item call API add
        if (Array.isArray(items)) {
          for (const item of items) {
            if (item && item.address) {
              const stickerData = {
                address: item.address,
                name: item.name || item.address,
                image_url: item.image_url || item.image || '/static/img/placeholder.png',
                skin_tone: item.skin_tone || item.skin || item.skinTone || 'Unknown',
                emotion: (item.emotion || item.emotion_tag || 'NEUTRAL').toUpperCase(),
                score: Number(item.score || item.total_pwr || item.power || 0) || 0,
                wallet_address: item.wallet_address || item.wallet || 'unknown',
                owner: item.owner || item.wallet_address || item.wallet || 'unknown',
                recipient: item.recipient || null
              };
              try {
                await apiAddSticker(stickerData);
                appState.basket.set(stickerData.address, stickerData);
              } catch (e) {
                console.warn('Failed to add imported sticker', e);
              }
            }
          }
        }
        saveBasketToStorage(appState);
        ui.showMessage('Basket imported successfully!', 'success');
        if (domElements.onBasketUpdated) domElements.onBasketUpdated();
        if (domElements.updatePortfolioIfActive) domElements.updatePortfolioIfActive();
      } catch (err) {
        ui.showMessage('Failed to import basket: ' + err.message, 'error');
        console.error('Basket import error:', err);
      }
      event.target.value = '';
    });
  }
  
  // Add sidebar toggle functionality
  var sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
  var sidebar = document.getElementById('sidebar');
  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('expanded');
      
      // Перерендерить корзину после завершения CSS-анимации
      const handleTransitionEnd = () => {
        // Небольшая задержка, чтобы браузер пересчитал размеры контейнера
        setTimeout(() => {
          updateOriginalBaskets(appState, domElements);
          updateExchangeBaskets(appState, portfolioState, exchangeState, domElements);
        }, 50);
        sidebar.removeEventListener('transitionend', handleTransitionEnd);
      };
      
      sidebar.addEventListener('transitionend', handleTransitionEnd);
    });
  }
  
  ui.initializeBasketTabs(appState, portfolioState, exchangeState, domElements);
  console.log('Event listeners initialized');
  // NOTE: basket is now loaded by outer initialization sequence (DOMContentLoaded listener),
  // so we don’t duplicate the work here. The previous version re-read storage twice which
  // caused the basket UI to blink/refresh on page reload.
};
ui.switchTab = async function(tabName, appState, exchangeState, portfolioState, domElements) {
  console.log('switchTab called with', tabName);
  domElements.tabBtns.forEach(btn => btn.classList.remove('active'));
  domElements.tabPanes.forEach(pane => pane.classList.remove('active'));
  var tabBtn = document.querySelector('[data-tab="' + tabName + '"]');
  if (tabBtn) tabBtn.classList.add('active');
  var pane = document.getElementById(tabName);
  if (pane) pane.classList.add('active');
  saveActiveTab(tabName);
  if (tabName === 'portfolio') {
    console.log('Activating portfolio tab');
    if (domElements.loadPortfoliosCallback) {
      domElements.loadPortfoliosCallback().catch(err => console.error('Failed to load portfolio', err));
    }
  }
  if (tabName === 'synergies' || tabName === 'synergy') {
    console.log('Activating synergy tab');
    if (domElements.initSynergyCallback) {
      domElements.initSynergyCallback().catch(err => console.error('Failed to init synergy tab', err));
    }
  }
  if (tabName === 'basket') {
    console.log('Activating basket tab');
    if (appState && domElements) {
      try {
        // refresh from server to ensure up-to-date
        await loadBasketFromServer(appState, domElements);
        updateExchangeBaskets(appState, portfolioState, exchangeState, domElements);
      } catch (err) {
        console.error('Error updating exchange baskets on tab switch', err);
      }
    }
    var origBtn = document.querySelector('.inner-tab-btn[data-inner-tab="basket-orig"]');
    if (origBtn) origBtn.click();
  }
};
ui.initializeBasketTabs = function(appState, portfolioState, exchangeState, domElements) {
  var buttons = document.querySelectorAll('.inner-tab-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.inner-tab-pane').forEach(p => p.classList.remove('active'));
      var target = document.getElementById(btn.dataset.innerTab);
      if (target) target.classList.add('active');
      if (btn.dataset.innerTab === 'basket-exchange') {
        updateExchangeBaskets(appState, portfolioState, exchangeState, domElements);
      } else if (btn.dataset.innerTab === 'basket-orig') {
        if (appState && domElements) {
          try {
            updateOriginalBaskets(appState, domElements);
          } catch (e) {
            console.error('Error updating original baskets', e);
          }
        }
      } else if (btn.dataset.innerTab === 'basket-new-portfolio') {
        if (appState && portfolioState && exchangeState) {
          try {
            if (typeof renderNewPortfolio === 'function') {
              renderNewPortfolio(appState, portfolioState, exchangeState, domElements).catch(err => console.error('new portfolio render failed', err));
            }
          } catch (e) {
            console.error('Error rendering new portfolio', e);
          }
        }
      }
    });
  });
};
ui.showMessage = function(message, type) {
  type = type || 'info';
  var messageEl = document.createElement('div');
  messageEl.className = 'message message-' + type;
  messageEl.textContent = message;
  messageEl.style.cssText = 'position: fixed; top: 20px; right: 20px; padding: 15px 20px; background: ' + (type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196f3') + '; color: white; border-radius: 4px; font-weight: bold; z-index: 9999;';
  document.body.appendChild(messageEl);
  setTimeout(() => messageEl.remove(), 3000);
};
// original loadWallets implementation from ui.js with API calls
ui.loadWallets = async function(appState, domElements) {
  if (!domElements.walletsInput) return;

  const walletLines = domElements.walletsInput.value
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);

  if (walletLines.length === 0) {
    ui.showMessage('Please enter at least one wallet address', 'error');
    return;
  }

  domElements.loadBtn.disabled = true;
  domElements.progressContainer.style.display = 'block';

  try {
    const response = await fetch(`${API_URL}/load-wallets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(walletLines)
    });

    const data = await response.json();

    // Update progress
    let successCount = 0;
    let errorCount = 0;

    if (data.results) {
      data.results.forEach(result => {
        if (result.status === 'success') successCount++;
        if (result.status === 'error') {
          console.error(`Error loading ${result.wallet}: ${result.error}`);
          errorCount++;
        }
        if (result.progress !== undefined) {
          domElements.progressFill.style.width = (result.progress * 100) + '%';
          domElements.progressText.textContent = `Loading wallet ${Math.round(result.progress * 100)}%`;
        }
      });
    }

    domElements.progressContainer.style.display = 'none';

    if (errorCount > 0) {
      ui.showMessage(`Loaded ${successCount} wallets, ${errorCount} errors`, 'warning');
    } else {
      ui.showMessage('✅ All wallets loaded successfully!', 'success');
    }

    // Fetch the list of wallets that were loaded
    console.log('Fetching wallet list from backend...');
    const walletsResponse = await api.fetchWallets();
    const walletsInDb = walletsResponse.wallets || [];
    console.log('Wallets in DB:', walletsInDb.length, walletsInDb);

    // keep full wallet objects rather than just addresses; dropdown and exchange logic
    appState.walletsInDb = walletsInDb;
    // populate textarea with current wallets
    if (domElements.walletsInput) {
      domElements.walletsInput.value = walletsInDb.map(w=>w.address).join('\n');
    }

    // После загрузки кошельков — инициализация синергий
    try {
      ui.showMessage('⏳ Инициализация синергий...', 'info');
      const resp = await fetch(`${API_URL}/initialize-synergies`, { method: 'POST' });
      const res = await resp.json();
      if (res.status === 'ok') {
        ui.showMessage('✅ Синергии успешно инициализированы!', 'success');
      } else {
        ui.showMessage('⚠️ Ошибка инициализации синергий: ' + (res.error || 'unknown'), 'warning');
      }
    } catch (e) {
      ui.showMessage('⚠️ Ошибка инициализации синергий: ' + (e.message || e), 'warning');
    }
    // Refresh portfolio and synergy data
    if (domElements.loadPortfoliosCallback) {
      console.log('Loading portfolios...');
      await domElements.loadPortfoliosCallback();
    }
    if (domElements.initSynergyCallback) {
      console.log('Initializing synergy tab...');
      await domElements.initSynergyCallback();
    }

  } catch (error) {
    ui.showMessage(`Error: ${error.message}`, 'error');
    console.error('Load wallets error:', error);
  } finally {
    domElements.loadBtn.disabled = false;
  }
};
ui.clearDatabase = async function(appState, domElements) {
  if (!confirm('Are you sure you want to clear the database? This cannot be undone.')) {
    return;
  }
  domElements.clearBtn.disabled = true;
  try {
    var response = await fetch(API_URL + '/database', {
      method: 'DELETE'
    });
    await response.json();
    ui.showMessage('✅ Database cleared', 'success');
    appState.walletsInDb = [];
    appState.basket.clear();
    appState.currentSynergies = {};
    if (domElements.loadPortfoliosCallback) {
      await domElements.loadPortfoliosCallback();
    }
    if (domElements.initSynergyCallback) {
      await domElements.initSynergyCallback();
    }
  } catch (error) {
    ui.showMessage('Error: ' + error.message, 'error');
    console.error('Clear database error:', error);
  } finally {
    domElements.clearBtn.disabled = false;
  }
};
// --- End ui.js ---

// ===============================
// SECTION: Module placeholders
// ===============================
// Placeholder objects for modules; real implementations attached later
var basket = {};
var portfolio = {};
var synergy = {};
// real module code is inserted further down in this file


// ===============================
// SECTION: utils/storage.js
// ===============================
var BASKET_STORAGE_KEY = 'exchange_basket_v1';
var ACTIVE_TAB_KEY = 'active_tab';

// -------------------- API helpers for basket --------------------
async function apiGetBasket() {
  const resp = await fetch(`${API_URL}/basket/stickers`);
  if (!resp.ok) throw new Error('failed to fetch basket');
  const data = await resp.json();
  // DEBUG: Log what backend sends
  console.log('DEBUG: Raw data from /basket/stickers backend:', data);
  if (Array.isArray(data) && data.length > 0) {
    console.log('DEBUG: First sticker from backend:', data[0]);
    console.log('DEBUG: Synergies field in first sticker:', data[0].synergies);
  }
  return data;
}

async function apiAddSticker(stickerData) {
  const resp = await fetch(`${API_URL}/basket/sticker/add`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      sticker_address: stickerData.address,
      owner: stickerData.owner,
      recipient: stickerData.recipient
    })
  });
  if (!resp.ok) throw new Error('failed to add sticker to basket');
  return await resp.json();
}

async function apiUpdateSticker(address, recipient) {
  const resp = await fetch(`${API_URL}/basket/sticker/update`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ sticker_address: address, recipient })
  });
  if (!resp.ok) throw new Error('failed to update basket sticker');
  return await resp.json();
}

async function apiDeleteSticker(address) {
  const resp = await fetch(`${API_URL}/basket/sticker/delete`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ sticker_address: address })
  });
  if (!resp.ok) throw new Error('failed to delete basket sticker');
  return await resp.json();
}

async function apiClearBasket() {
  const resp = await fetch(`${API_URL}/basket/clear`, {method:'POST'});
  if (!resp.ok) throw new Error('failed to clear basket');
  return await resp.json();
}

// save basket locally (server sync occurs in individual operations)
function saveBasketToStorage(appState, serverName) {
  try {
    var items = Array.from(appState.basket.values());
    localStorage.setItem(BASKET_STORAGE_KEY, JSON.stringify(items));
  } catch (err) {
    console.warn('Failed to save basket to local storage', err);
  }
}

function loadBasketFromStorage() {
  try {
    var raw = localStorage.getItem(BASKET_STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (err) {
    console.warn('Failed to load basket from local storage', err);
    return [];
  }
}

// attempt to fetch latest basket from server and replace local state
async function loadBasketFromServer(appState, domElements) {
  try {
    const items = await apiGetBasket();
    if (Array.isArray(items)) {
      appState.basket.clear();
      items.forEach(it => {
        if (it && it.address) {
          appState.basket.set(it.address, {
            address: it.address,
            name: it.name || it.address,
            image_url: it.image_url || '',
            skin_tone: it.skin_tone || '',
            emotion: it.emotion || '',
            score: it.score || 0,
            attr_value: it.attr_value || 0,
            synergy_bonus: it.synergy_bonus || 0,
            name_value: it.name_value || 0,
            wallet_address: it.wallet_address || '',
            owner: it.owner || '',
            recipient: it.recipient || null,
            attributes: it.attributes || {},
            synergies: it.synergies || []  // ADD SYNERGIES FIELD
          });
        }
      });
      if (domElements && domElements.onBasketUpdated) domElements.onBasketUpdated();
    }
  } catch (e) {
    console.debug('Error loading basket from server', e);
  }
}


function saveActiveTab(tabName) {
  try {
    localStorage.setItem(ACTIVE_TAB_KEY, tabName);
  } catch (err) {
    console.warn('Failed to save active tab', err);
  }
}

function loadActiveTab() {
  try {
    return localStorage.getItem(ACTIVE_TAB_KEY);
  } catch (err) {
    return null;
  }
}
// --- End storage.js ---

// ===============================
// SECTION: utils/helpers.js
// ===============================
function shortAddr(addr) {
  if (!addr) return 'unknown';
  return addr.slice(0, 6) + '...' + addr.slice(-4);
}
function isInBasket(stickerAddress, appState) {
  return appState.basket.has(stickerAddress);
}
function adjustPortfolio(wallet, skin, delta, portfolioState) {
  if (!wallet) return;
  if (!portfolioState.adjustments[wallet]) {
    portfolioState.adjustments[wallet] = {};
  }
  portfolioState.adjustments[wallet][skin] =
    (portfolioState.adjustments[wallet][skin] || 0) + delta;
}
function calculateWalletDelta(wallet, skin, portfolioState) {
  const m = portfolioState.adjustments[wallet] || {};
  if (skin) {
    return m[skin] || 0;
  }
  return Object.values(m).reduce((s, v) => s + v, 0);
}
function buildFilterParams(selectedSkin, selectedGroup) {
  const params = [];
  if (selectedSkin && selectedSkin !== 'ALL') {
    params.push(`skin_tone=${encodeURIComponent(selectedSkin)}`);
  }
  if (selectedGroup && selectedGroup !== 'ALL') {
    params.push(`attribute_group=${encodeURIComponent(selectedGroup)}`);
  }
  return params;
}
// --- End helpers.js ---

// ===============================
// SECTION: utils/stats.js
// ===============================
function computePortfolioStats(stickers, filterSkin = null, collectionSynergy = null, prebuiltTeams = null) {
  let stickerCount = 0;
  let stickerPower = 0;
  let synergyPower = 0;
  let teamCount = 0;
  let fullCount = 0;
  const bySkin = {};

  // if we were given prebuiltTeams, compute sticker count/power from those teams
  // (this handles the "new portfolio" case where the API response already
  // defines which stickers were used to build teams) – we still need the
  // original `stickers` array for skins grouping when building teams later.
  if (prebuiltTeams) {
    const flatTeams = Array.isArray(prebuiltTeams)
      ? prebuiltTeams
      : Object.values(prebuiltTeams).flat();
    flatTeams.forEach(team => {
      (team.stickers || []).forEach(s => {
        const skin = s.skin_tone || 'Unknown';
        if (filterSkin && skin !== filterSkin) return;
        const attrVal = s.attr_value || 0;
        const nameVal = s.name_value || 0;
        const stickerSyn = s.synergy_bonus || 0;
        stickerCount++;
        stickerPower += attrVal + nameVal + stickerSyn;
      });
    });
    // also compute team counts from prebuiltTeams now, below we will override again
  } else {
    stickers.forEach(s => {
      const skin = s.skin_tone || 'Unknown';
      if (filterSkin && skin !== filterSkin) return;
      const attrVal = s.attr_value || 0;
      const nameVal = s.name_value || 0;
      const stickerSyn = s.synergy_bonus || 0;
      stickerCount++;
      stickerPower += attrVal + nameVal + stickerSyn;
      if (!bySkin[skin]) bySkin[skin] = [];
      bySkin[skin].push(s);
    });
  }

  if (prebuiltTeams) {
    let flat = [];
    if (Array.isArray(prebuiltTeams)) flat = prebuiltTeams;
    else flat = Object.values(prebuiltTeams).flat();
    teamCount = flat.length;
    fullCount = flat.filter(t => t.is_complete || t.isComplete).length;
  }
  const buildTeams = arr => {
    const teams = [];
    const emotionMap = {};
    arr.forEach(s => {
      const e = s.emotion || 'NEUTRAL';
      if (!emotionMap[e]) emotionMap[e] = [];
      emotionMap[e].push(s);
    });
    Object.keys(emotionMap).forEach(e => {
      emotionMap[e].sort((a, b) => (b.score || 0) - (a.score || 0));
    });
    const used = {};
    Object.keys(emotionMap).forEach(e => (used[e] = 0));
    while (true) {
      const avail = Object.keys(emotionMap).filter(e => used[e] < emotionMap[e].length);
      if (!avail.length) break;
      const scored = avail
        .map(e => ({
          emotion: e,
          power: (emotionMap[e][used[e]] && emotionMap[e][used[e]].score) || 0
        }))
        .sort((a, b) => b.power - a.power);
      const selected = scored.slice(0, 7).map(s => s.emotion);
      const teamStickers = [];
      selected.forEach(em => {
        const st = emotionMap[em][used[em]];
        if (st) { teamStickers.push(st); used[em]++; }
      });
      if (teamStickers.length) {
        teams.push({ emotions: selected, stickers: teamStickers, isComplete: selected.length === 7 && teamStickers.length === 7 });
      } else break;
    }
    return teams;
  };
  let allTeams = [];
  if (!prebuiltTeams) {
    if (filterSkin) {
      const arr = bySkin[filterSkin] || [];
      const t = buildTeams(arr);
      teamCount = t.length;
      fullCount = t.filter(x => x.isComplete).length;
      allTeams = allTeams.concat(t);
    } else {
      Object.values(bySkin).forEach(arr => {
        const t = buildTeams(arr);
        teamCount += t.length;
        fullCount += t.filter(x => x.isComplete).length;
        allTeams = allTeams.concat(t);
      });
    }
  } else {
    let flat;
    if (Array.isArray(prebuiltTeams)) {
      flat = prebuiltTeams;
    } else {
      flat = filterSkin && prebuiltTeams[filterSkin]
        ? prebuiltTeams[filterSkin]
        : Object.values(prebuiltTeams).flat();
    }
    allTeams = flat.map(t => ({ stickers: t.stickers || [] }));
  }
  if (collectionSynergy) {
    allTeams.forEach(team => {
      const synObj = computeTeamSynergy(team.stickers || [], collectionSynergy);
      synergyPower += synObj.total || 0;
    });
  }
  const teamPower = fullCount * 350;
  const totalPower = stickerPower + teamPower + synergyPower;

  // compute counts of teams by size (number of stickers in team)
  const teamSizeCounts = {};
  allTeams.forEach(team => {
    const len = (team.stickers || []).length;
    teamSizeCounts[len] = (teamSizeCounts[len] || 0) + 1;
  });

  return {
    totalPower,
    stickerCount,
    teamCount,
    fullCount,
    stickerPower,
    synergyPower,
    teamPower,
    teamSizeCounts
  };
}

// Compute attribute counts for a set of wallets (or recipients) given grouped sticker lists.
// groupedStickers: {groupKey: [sticker, ...]}
// attributesPriority: list of attribute names that should appear first in the table.
function computeAttributeCountsByGroup(groupedStickers, attributesPriority) {
  const allAttrs = new Set(attributesPriority || []);
  Object.values(groupedStickers).forEach(list => {
    (list || []).forEach(st => {
      const attrs = st.attributes || {};
      Object.values(attrs).forEach(v => {
        if (v == null) return;
        if (Array.isArray(v)) {
          v.forEach(x => {
            if (x != null) allAttrs.add(String(x));
          });
        } else {
          allAttrs.add(String(v));
        }
      });
    });
  });

  const orderedAttrs = [
    ...(attributesPriority || []),
    ...Array.from(allAttrs).filter(a => !(attributesPriority || []).includes(a)).sort()
  ];

  const walletKeys = Object.keys(groupedStickers);
  const table = {};
  orderedAttrs.forEach(attr => {
    const row = {};
    let hasAny = false;
    walletKeys.forEach(key => {
      let count = 0;
      (groupedStickers[key] || []).forEach(st => {
        const attrs = st.attributes || {};
        Object.values(attrs).forEach(v => {
          if (v == null) return;
          if (Array.isArray(v)) {
            v.forEach(x => { if (String(x) === attr) count++; });
          } else if (String(v) === attr) {
            count++;
          }
        });
      });
      if (count > 0) {
        row[key] = count;
        hasAny = true;
      }
    });

    // Ensure priority attributes are always present (even if zero)
    if (!hasAny && (attributesPriority || []).includes(attr)) {
      walletKeys.forEach(key => { row[key] = 0; });
      hasAny = true;
    }

    // Always include priority attributes, even if they have zero counts
    if ((attributesPriority || []).includes(attr)) {
      if (!hasAny) {
        walletKeys.forEach(key => { row[key] = 0; });
      }
      table[attr] = row;
    } else if (hasAny) {
      table[attr] = row;
    }
  });

  return table;
}

function renderAttributeStatsTable(container, attributeCounts, attributesPriority) {
  if (!container || !attributeCounts) return;
  // Show table even if only priority attributes with zero counts
  if (Object.keys(attributeCounts).length === 0) return;

  const wallets = new Set();
  Object.values(attributeCounts).forEach(row => {
    Object.keys(row).forEach(w => wallets.add(w));
  });
  const walletList = Array.from(wallets).sort();

  const rows = Object.entries(attributeCounts);
  const visibleRowsCount = 8;
  const priorityAttrs = new Set(attributesPriority || []);

  const firstWalletKey = walletList[0] || null;
  rows.sort(([aAttr, aRow], [bAttr, bRow]) => {
    const aIsPriority = priorityAttrs.has(aAttr) ? 1 : 0;
    const bIsPriority = priorityAttrs.has(bAttr) ? 1 : 0;
    if (aIsPriority !== bIsPriority) return bIsPriority - aIsPriority;

    const aCount = firstWalletKey ? (aRow[firstWalletKey] || 0) : 0;
    const bCount = firstWalletKey ? (bRow[firstWalletKey] || 0) : 0;
    if (aCount !== bCount) return bCount - aCount;

    return aAttr.localeCompare(bAttr);
  });

  let hasExtraRows = false;

  const table = document.createElement('table');
  table.className = 'attribute-stats-table';
  table.style.cssText = 'width:auto;border-collapse:collapse;font-size:12px;margin-bottom:12px;background:rgba(30,40,50,0.8);border:1px solid #45688a;';

  const headerRow = table.insertRow();
  headerRow.style.background = 'rgba(20,30,40,0.9)';
  const attrHeader = headerRow.insertCell();
  attrHeader.textContent = 'Attribute';
  attrHeader.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#fbbf24;min-width:120px;';
  walletList.forEach(wallet => {
    const cell = headerRow.insertCell();
    const shortWallet = wallet === 'unknown' ? '(unknown)' : helpers.shortAddr(wallet);
    cell.textContent = shortWallet;
    cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#39a1ff;text-align:center;min-width:120px;';
  });

  rows.forEach(([attr, row], index) => {
    const tr = table.insertRow();
    const isPriority = priorityAttrs.has(attr);
    const shouldHide = index >= visibleRowsCount && !isPriority;
    if (shouldHide) {
      tr.className = 'attribute-stats-extra-row';
      tr.style.display = 'none';
      hasExtraRows = true;
    }

    const attrCell = tr.insertCell();
    attrCell.textContent = attr;
    attrCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;';

    walletList.forEach(wallet => {
      const cell = tr.insertCell();
      const val = row[wallet] || 0;
      cell.textContent = val > 0 ? val : '-';
      cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;font-size:12px;';
    });
  });

  const wrapper = document.createElement('div');
  wrapper.className = 'attribute-stats-table-wrapper';
  wrapper.appendChild(table);

  if (hasExtraRows) {
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.textContent = 'Показать таблицу полностью';
    toggleBtn.dataset.expanded = 'false';
    toggleBtn.style.cssText = 'margin-top:6px;padding:6px 10px;font-size:12px;border-radius:4px;border:1px solid #4f82a5;background:#123148;color:#fefefe;cursor:pointer;';

    toggleBtn.addEventListener('click', () => {
      const expanded = toggleBtn.dataset.expanded === 'true';
      table.querySelectorAll('.attribute-stats-extra-row').forEach(r => {
        r.style.display = expanded ? 'none' : '';
      });
      if (expanded) {
        toggleBtn.textContent = 'Показать таблицу полностью';
        toggleBtn.dataset.expanded = 'false';
      } else {
        toggleBtn.textContent = 'Свернуть дополнительные атрибуты';
        toggleBtn.dataset.expanded = 'true';
      }
    });
    wrapper.appendChild(toggleBtn);
  }

  container.appendChild(wrapper);
}

function computeTeamSynergy(team_stickers, collectionSynergy) {
  const TEAM_SYNERGY_TRAITS = {
    logo: 'Logos',
    bracelet: 'Bracelet',
    earrings: 'Earrings'
  };
  if (!collectionSynergy || !collectionSynergy.bonus_table) {
    console.warn('computeTeamSynergy: missing collectionSynergy or bonus_table');
    return { logo: 0, bracelet: 0, earrings: 0, total: 0 };
  }
  if (!Array.isArray(team_stickers)) {
    if (team_stickers && typeof team_stickers === 'object') {
      team_stickers = Object.values(team_stickers);
    } else {
      team_stickers = [];
    }
  }
  const synergyBonuses = {1:0,2:0,3:0,4:400,5:500,6:700,7:1000};
  const result = { logo:0, bracelet:0, earrings:0, total:0 };
  Object.entries(TEAM_SYNERGY_TRAITS).forEach(([key, trait]) => {
    const counts = {};
    team_stickers.forEach(st => {
      const attrs = st.attributes || {};
      Object.entries(attrs).forEach(([tName, tVal]) => {
        if (!tName) return;
        let match = false;
        if (key==='logo') {
          match = tName.toLowerCase().includes('logo');
        } else {
          match = tName.toLowerCase() === trait.toLowerCase();
        }
        if (!match) return;
        const values = Array.isArray(tVal) ? tVal : [tVal];
        values.forEach(v => {
          if (!v) return;
          let normalizedV = String(v).trim();
          if (key==='logo') {
            const words = normalizedV.split(/\s+/);
            if (words.length > 1) normalizedV = words[words.length-1];
          }
          counts[normalizedV] = (counts[normalizedV] || 0) + 1;
        });
      });
    });
    let maxCount=0;
    let maxValue=null;
    Object.entries(counts).forEach(([val,c])=>{
      if(c>maxCount){maxCount=c;maxValue=val;}
    });
    maxCount = Math.min(maxCount,7);
    const bonus = synergyBonuses[maxCount] || 0;
    result[key] = bonus;
    result.total += bonus;
    result[`${key}Count`] = maxCount;
    if (maxValue!==null) result[`${key}Value`] = maxValue;
  });
  return result;
}
// --- End stats.js ---

// ===============================
// SECTION: utils/render.js
// ===============================
/**
 * Create basket card with rarity and synergy badges at the bottom
 */
function createBasketCard(sticker, address, callbacks = {}) {
  const item = document.createElement('div');
  item.className = 'basket-item';
  item.style.width = '140px';
  item.style.boxSizing = 'border-box';
  item.style.display = 'flex';
  item.style.flexDirection = 'column';
  item.style.alignItems = 'center';
  item.style.justifyContent = 'flex-start';
  item.style.padding = '10px';
  item.style.borderRadius = '8px';
  item.style.background = 'rgba(15,20,25,0.6)';
  item.innerHTML = `
    <div style="display:flex;width:100%;justify-content:space-between;">
      <button class="basket-item-remove" data-remove-address="${address}">✕</button>
      <button class="basket-item-send" data-send-address="${address}">📤</button>
    </div>
    <img src="${sticker.image_url||PLACEHOLDER_IMAGE}" alt="${sticker.name}" style="width:100px;height:100px;object-fit:cover;border-radius:8px;margin:6px 0">
    <div class="basket-item-name" style="font-size:13px;text-align:center;line-height:1.1;">${sticker.name}</div>
    <div class="basket-item-owner" style="font-size:11px;color:#aaa">От: ${shortAddr(sticker.owner||'')}</div>
    <div class="basket-item-recipient" style="font-size:11px;color:#aaa">К: ${sticker.recipient?shortAddr(sticker.recipient):'-'}</div>
    <div class="basket-item-emotion" style="font-size:12px;color:#9be7ff">${sticker.emotion||'NEUTRAL'}</div>
    <div class="basket-item-value" style="font-size:13px;color:#fbbf24;margin-top:6px">💰 ${sticker.score||0} PWR</div>
  `;
  
  // Add rarity badge if available
  const score = Math.round(sticker.score || 0);
  const rarityTier = getRarityTier(score);
  if (rarityTier) {
    const rarityBadgeDiv = document.createElement('div');
    rarityBadgeDiv.style.cssText = 'margin-top:6px;width:100%;';
    const rarityBadge = document.createElement('div');
    rarityBadge.className = 'synergy-badge ' + (rarityTier.class || '');
    rarityBadge.style.background = 'linear-gradient(135deg, ' + rarityTier.color + ' 0%, ' + rarityTier.color + ' 100%)';
    rarityBadge.style.borderColor = rarityTier.color;
    rarityBadge.style.fontSize = '10px';
    rarityBadge.textContent = rarityTier.label;
    rarityBadgeDiv.appendChild(rarityBadge);
    item.appendChild(rarityBadgeDiv);
  }
  
  // Add synergy badges if available (унифицировано с createStickerCard)
  if (Array.isArray(sticker.synergies) && sticker.synergies.length > 0) {
    const synergiesContainer = document.createElement('div');
    synergiesContainer.style.cssText = 'display:flex;flex-direction:column;gap:2px;margin-top:4px;width:100%';
    sticker.synergies.forEach(function(syn) {
      const maxRow = syn.max_row_count || 4;
      let labelColor;
      if (maxRow === 4) labelColor = '#39a1ff';
      else if (maxRow === 5) labelColor = '#9b5cff';
      else if (maxRow === 6) labelColor = '#ffd700';
      else if (maxRow === 7) labelColor = '#ff66b2';
      else labelColor = '#808080';
      const emoji = (typeof SYNERGY_EMOJI_MAP !== 'undefined' && SYNERGY_EMOJI_MAP[syn.group_name]) ? SYNERGY_EMOJI_MAP[syn.group_name] : (syn.emoji || '✨');
      const attrValue = syn.attr_value || 'N/A';
      const label = document.createElement('div');
      label.className = 'synergy-badge';
      label.style.background = 'linear-gradient(135deg, ' + labelColor + ' 0%, ' + labelColor + ' 100%)';
      label.style.borderColor = labelColor;
      label.style.fontSize = '10px';
      label.textContent = emoji + ' ' + attrValue;
      label.title = (syn.group_name || 'Unknown') + ': ' + attrValue + ' (' + maxRow + ' атрибутов)';
      synergiesContainer.appendChild(label);
    });
    item.appendChild(synergiesContainer);
  }
  
  const removeBtn = item.querySelector('.basket-item-remove');
  if(removeBtn && callbacks.onRemove){ removeBtn.addEventListener('click',()=>callbacks.onRemove(address)); }
  const sendBtn = item.querySelector('.basket-item-send');
  if(sendBtn && callbacks.onSend){ sendBtn.addEventListener('click',e=>{e.stopPropagation();callbacks.onSend(sendBtn,address);});}
  return item;
}

/**
 * Render basket items grouped by wallet, then by skin tone within each wallet
 */
function renderBasketGroup(container, title, stickers, callbacks = {}) {
  const items = stickers.map(s => ({ address: s.address, sticker: s }));
  const totalPwr = items.reduce((acc, it) => acc + (it.sticker.score || 0), 0);
  const section = document.createElement('div');
  section.className = 'basket-wallet-section';
  section.style.display = 'block';
  section.style.width = '100%';
  section.style.boxSizing = 'border-box';
  section.style.padding = '8px 0';
  const header = document.createElement('div');
  header.className = 'basket-wallet-header';
  header.innerHTML = `<strong>${title}</strong> — 💰 ${totalPwr} PWR`;
  section.appendChild(header);
  
  // Group by skin tone (tribe)
  const bySkinTone = {};
  items.forEach(item => {
    const skin = (item.sticker.skin_tone || item.sticker.skin || item.sticker.skinTone || 'Unknown').toString();
    if (!bySkinTone[skin]) bySkinTone[skin] = [];
    bySkinTone[skin].push(item);
  });
  
  // Sort skin tones
  let sortedSkins = Object.keys(bySkinTone);
  sortedSkins.sort((a, b) => {
    const sa = a.toLowerCase();
    const sb = b.toLowerCase();
    if (typeof SKIN_ORDER !== 'undefined' && Array.isArray(SKIN_ORDER)) {
      const ai = SKIN_ORDER.findIndex(x => (x||'').toString().toLowerCase() === sa);
      const bi = SKIN_ORDER.findIndex(x => (x||'').toString().toLowerCase() === sb);
      if (ai !== -1 || bi !== -1) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    }
    return a.localeCompare(b);
  });
  
  // Prepare groups: sort items within each group by power
  const groups = [];
  sortedSkins.forEach(skinTone => {
    const skinItems = bySkinTone[skinTone];
    skinItems.sort((a, b) => (b.sticker.score || 0) - (a.sticker.score || 0));
    groups.push({
      skinTone,
      items: skinItems,
      totalCount: skinItems.length,
      totalPwr: skinItems.reduce((acc, it) => acc + (it.sticker.score || 0), 0)
    });
  });
  
  // Create rows with dynamic max cards per row based on ACTUAL container width
  // Рассчитываем количество карточек на основе реальной ширины контейнера
  let CARDS_PER_ROW = 14; // Default fallback
  
  // Попробуем получить ширину контейнера
  if (container && container.clientWidth > 0) {
    const containerWidth = container.clientWidth;
    const cardWidth = 140; // Ширина одной карточки (в пикселях)
    const gapBetweenCards = 10; // Зазор между карточками
    const availableWidth = containerWidth - 30; // Минус отступы контейнера
    
    // Вычисляем сколько карточек может влезть в ширину
    CARDS_PER_ROW = Math.max(1, Math.floor(availableWidth / (cardWidth + gapBetweenCards)));
  }
  
  //Ограничиваем максимум в зависимости от состояния меню
  const sidebar = document.getElementById('sidebar');
  const isExpanded = sidebar && sidebar.classList.contains('expanded');
  const maxCardsPerRow = isExpanded ? 14 : 17;
  CARDS_PER_ROW = Math.min(CARDS_PER_ROW, maxCardsPerRow);
  
  const rows = [];
  let currentRow = [];
  let currentRowCount = 0;
  
  // Process each group and distribute into rows
  groups.forEach(group => {
    let itemsUsed = 0;
    
    while (itemsUsed < group.items.length) {
      const cardsLeftInRow = CARDS_PER_ROW - currentRowCount;
      
      if (cardsLeftInRow === 0) {
        // Current row is full, start new row
        rows.push(currentRow);
        currentRow = [];
        currentRowCount = 0;
        continue;
      }
      
      const itemsLeftInGroup = group.items.length - itemsUsed;
      const itemsToTake = Math.min(itemsLeftInGroup, cardsLeftInRow);
      
      // Create row entry for this portion of the group
      const rowEntry = {
        skinTone: group.skinTone,
        items: group.items.slice(itemsUsed, itemsUsed + itemsToTake),
        totalCountInGroup: group.totalCount,
        totalPwrInGroup: group.totalPwr
      };
      
      currentRow.push(rowEntry);
      currentRowCount += itemsToTake;
      itemsUsed += itemsToTake;
      
      if (currentRowCount === CARDS_PER_ROW) {
        rows.push(currentRow);
        currentRow = [];
        currentRowCount = 0;
      }
    }
  });
  
  if (currentRow.length > 0) {
    rows.push(currentRow);
  }
  
  // Render rows
  const mainContainer = document.createElement('div');
  mainContainer.style.cssText = 'display:flex;flex-direction:column;gap:12px;';
  
  rows.forEach(row => {
    const rowDiv = document.createElement('div');
    rowDiv.style.cssText = 'display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap;';
    
    row.forEach(rowEntry => {
      // Group header and cards container
      const groupContainer = document.createElement('div');
      groupContainer.style.cssText = 'display:flex;flex-direction:column;';
      
      // Group header
      const groupHeader = document.createElement('div');
      groupHeader.style.cssText = 'font-size:11px;color:#9be7ff;margin-bottom:6px;font-weight:600;white-space:nowrap;padding:0 4px;';
      groupHeader.innerHTML = `🎨 ${rowEntry.skinTone} <br/> 💰 ${rowEntry.totalPwrInGroup} PWR (${rowEntry.items.length}/${rowEntry.totalCountInGroup})`;
      groupContainer.appendChild(groupHeader);
      
      // Cards in this group
      const cardsContainer = document.createElement('div');
      cardsContainer.style.cssText = 'display:flex;gap:10px;';
      
      rowEntry.items.forEach(({ address, sticker }) => {
        const card = createBasketCard(sticker, address, {
          onRemove: callbacks.onRemove,
          onSend: callbacks.onSend
        });
        cardsContainer.appendChild(card);
      });
      
      groupContainer.appendChild(cardsContainer);
      rowDiv.appendChild(groupContainer);
    });
    
    mainContainer.appendChild(rowDiv);
  });
  
  section.appendChild(mainContainer);
  container.appendChild(section);
}
// --- End render.js ---

// expose helper objects to modules
var helpers = {
  shortAddr,
  isInBasket,
  adjustPortfolio,
  calculateWalletDelta,
  buildFilterParams
};
var stats = {
  computePortfolioStats,
  computeTeamSynergy
};
var render = {
  renderBasketGroup,
  createBasketCard
};


// ===============================
// SECTION: Helper function recalcWalletPower
// ===============================
function recalcWalletPower(stickers) {
  /* Calculates total power of a wallet based on its stickers */
  return stickers.reduce(function(sum, s) {
    return sum + (s.total_value || s.power || s.score || 0);
  }, 0);
}
// --- End recalcWalletPower ---

// Initialize application state
const appState = createAppState();
const exchangeState = createExchangeState();
const portfolioState = createPortfolioState();
const exchangeMapping = {};

console.log('State objects created');

// Initialize DOM elements
const domElements = ui.initDOMElements();
console.log('DOM elements initialized:', Object.keys(domElements).length, 'elements');

// callback used throughout app to refresh basket UI after changes or when loading from storage
// originally this lived in ui.js; monolith lost the assignment so restore it here
if (domElements) {
  domElements.onBasketUpdated = function() {
    // update both exchange and original views
    try {
      updateExchangeBaskets(appState, portfolioState, exchangeState, domElements);
    } catch (e) { console.error('onBasketUpdated exchange error', e); }
    if (domElements.updateOriginalBaskets) {
      try {
        domElements.updateOriginalBaskets(appState, domElements);
      } catch (e) { console.error('onBasketUpdated original error', e); }
    }
    if (domElements.updatePortfolioIfActive) {
      try {
        domElements.updatePortfolioIfActive();
      } catch (e) { console.error('onBasketUpdated portfolio error', e); }
    }
  };
}

// Attach callback references for cross-module communication
// ===============================
// SECTION: config.js
// ===============================
/**
 * config.js — Unified card styling, constants, and configuration
 * (originally в config.js)
 */

// ===============================
// SECTION: utils/api.js
// ===============================
// API utilities copied from modules/utils/api.js
var api = {};
api.fetchStickerFromDb = async function(address) {
  if (!address) return null;
  try {
    const resp = await fetch(`${API_URL}/stickers/${encodeURIComponent(address)}`);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (err) {
    console.warn('Failed to fetch sticker from DB', err);
    return null;
  }
};
api.enrichStickerWithDb = async function(stickerData) {
  try {
    const db = await api.fetchStickerFromDb(stickerData.address);
    if (!db) return false;
    if (db.skin_tone && (!stickerData.skin_tone || stickerData.skin_tone === 'Unknown')) {
      stickerData.skin_tone = db.skin_tone;
    }
    if (db.image_url && (!stickerData.image_url || stickerData.image_url === PLACEHOLDER_IMAGE)) {
      stickerData.image_url = db.image_url;
    }
    if (db.name && (!stickerData.name || stickerData.name === stickerData.address)) {
      stickerData.name = db.name;
    }
    if (db.score && (!stickerData.score || stickerData.score === 0)) {
      stickerData.score = db.score;
    }
    return true;
  } catch (err) {
    return false;
  }
};
api.fetchWallets = async function() {
  try {
    const resp = await fetch(`${API_URL}/wallets`);
    return await resp.json();
  } catch (err) {
    console.error('Failed to fetch wallets', err);
    return { wallets: [] };
  }
};
api.fetchWalletStickers = async function(walletAddress, basket = null) {
  try {
    let url = `${API_URL}/wallets/${encodeURIComponent(walletAddress)}/stickers`;
    if (basket === true) {
      // use current basket adjustments from backend database
      url += '?basket=true';
    }
    const resp = await fetch(url);
    if (!resp.ok) {
      console.error(`Failed to fetch stickers for ${walletAddress}:`, resp.status);
      return { wallet: walletAddress, stickers: [] };
    }
    return await resp.json();
  } catch (err) {
    console.error(`Failed to fetch stickers for ${walletAddress}`, err);
    return { wallet: walletAddress, stickers: [] };
  }
};
api.fetchAllWalletsWithStickers = async function() {
  try {
    const resp = await fetch(`${API_URL}/wallets`);
    if (!resp.ok) return { results: [] };
    const data = await resp.json();
    const wallets = data.wallets || [];
    const results = await Promise.all(
      wallets.map(wallet => api.fetchWalletStickers(wallet.address))
    );
    return { results };
  } catch (err) {
    console.error('Failed to fetch all wallets with stickers', err);
    return { results: [] };
  }
};
api.clearDatabase = async function() {
  try {
    const resp = await fetch(`${API_URL}/database`, {
      method: 'DELETE'
    });
    return await resp.json();
  } catch (err) {
    console.error('Failed to clear database', err);
    return { status: 'error' };
  }
};
// simple client‑side cache to prevent repeated network calls
let _skinsCache = null;
let _synergiesCache = {};   // key: query string -> synergies object

api.fetchSkins = async function() {
  if (_skinsCache) {
    // return already‑fetched result immediately
    return { skins: _skinsCache };
  }
  const url = `${API_URL}/stickers/skins`;
  console.log('api.fetchSkins hitting', url);
  try {
    const resp = await fetch(url);
    if (!resp.ok) {
      if (resp.status === 400 || resp.status === 404) {
        console.warn('No skins found in database (database may be empty)');
        return { skins: [] };
      }
      console.error('Failed to fetch skins:', resp.status, resp.statusText);
      let text = await resp.text();
      console.debug('skins response body:', text);
      return { skins: [] };
    }
    try {
      const data = await resp.json();
      _skinsCache = data.skins || [];
      return { skins: _skinsCache };
    } catch (parseErr) {
      const text = await resp.text();
      console.error('Failed to parse skins JSON, response text:', text);
      throw parseErr;
    }
  } catch (err) {
    console.error('Failed to fetch skins', err);
    return { skins: [] };
  }
};

// optimal teams helper

// New: TribePowerBuilder API
api.fetchOptimalTeams = async function(walletAddress, useBasket = false) {
  console.log('api.fetchOptimalTeams called with', walletAddress, 'useBasket', useBasket);
  if (!walletAddress || walletAddress === 'unknown') {
    console.warn('fetchOptimalTeams skipped for invalid address', walletAddress);
    return { teams: [] };
  }
  try {
    var url = `${API_URL}/wallets/${encodeURIComponent(walletAddress)}/optimal-teams`;
    if (useBasket === true) {
      url += '?basket=true';
    }
    console.log('api.fetchOptimalTeams url=', url);
    var resp = await fetch(url);
    if (!resp.ok) {
      console.warn('Failed to fetch optimal teams for', walletAddress, resp.status);
      let body = await resp.text();
      console.debug('optimal-teams response body:', body);
      return { teams: [] };
    }
    try {
      return await resp.json();
    } catch (parseErr) {
      const text = await resp.text();
      console.error('Failed to parse optimal-teams JSON for', walletAddress, 'body', text);
      throw parseErr;
    }
  } catch (err) {
    console.error('Error fetching optimal teams for', walletAddress, err);
    return { teams: [] };
  }
};

// fetch all wallets with optimal teams (and stickers)
api.fetchAllWalletsWithTeams = async function(basket = null) {
  try {
    const resp = await fetch(`${API_URL}/wallets`);
    if (!resp.ok) return { results: [] };

    const data = await resp.json();
    const wallets = data.wallets || [];

    const results = await Promise.all(
      wallets.map(async wallet => {
        const addr = wallet.address;
        if (!addr) return null;
        const useBasket = !!basket;
        const [stickersResp, teamsResp] = await Promise.all([
          api.fetchWalletStickers(addr, useBasket),
          api.fetchOptimalTeams(addr, useBasket)
        ]);
        return {
          wallet: addr,
          address: addr,
          stickers: stickersResp.stickers || [],
          collection_synergy: stickersResp.collection_synergy || teamsResp.collection_synergy || {},
          teams: teamsResp.teams || {}
        };
      })
    );

    return { results };
  } catch (err) {
    console.error('Failed to fetch all wallets with teams', err);
    return { results: [] };
  }
};

// fetch attribute groups for synergy filters
api.fetchSynergies = async function(filters = '') {
  try {
    const url = `${API_URL}/stickers/synergies` + (filters ? ('?' + filters) : '');
    const resp = await fetch(url);
    if (!resp.ok) {
      if (resp.status === 400 || resp.status === 404) {
        console.warn('No synergies found in database (database may be empty)');
        return { synergies: {} };
      }
      console.error('Failed to fetch synergies:', resp.status, resp.statusText);
      return { synergies: {} };
    }
    return await resp.json();
  } catch (err) {
    console.error('Failed to fetch synergies', err);
    return { synergies: {} };
  }
};

api.fetchAttributeGroups = async function() {
  try {
    const resp = await fetch(`${API_URL}/stickers/attribute-groups`);
    if (!resp.ok) {
      if (resp.status === 400 || resp.status === 404) {
        console.warn('No attribute groups found');
        return { groups: [] };
      }
      return { groups: [] };
    }
    return await resp.json();
  } catch (err) {
    console.error('Failed to fetch attribute groups', err);
    return { groups: [] };
  }
};
// API Base URL - use current origin so caches can't stale a hard-coded value
var API_URL = window.location.origin;
var WALLET_COLORS = [
  'wallet-color-1',
  'wallet-color-2',
  'wallet-color-3',
  'wallet-color-4',
  'wallet-color-5'
];
var EMOTION_ORDER = [
  'In Love',
  'Greeting',
  'Capped',
  'Shoked',
  'Do Something',
  'To The Moon',
  'Wen TGE'
];
var SKIN_ORDER = [
  'Golden','Lunar','Demonic','Cosmic','Silver','Fairytale','Magical','Martian','Desert','Cavern','Forest','Urban','Beach','Mountain','Meadow','Swamp','Tropical','Taiga'
];
var STICKER_CARD_STYLE = {
  gridColumns: 160,
  gridGap: 12,
  width: 150,
  minHeight: 220,
  imageHeight: 100,
  fontSizeTitle: 11,
  fontSizeEmotion: 10,
  fontSizeScore: 12,
  fontSizeBreakdown: 11
};
var RARITY_TIERS = {
  unique: { min: 1500, label: '◆ UNIQUE', class: 'badge-unique', color: '#ff0000' },
  mythicPlus: { min: 1000, label: '★ MYTHIC+', class: 'badge-mythic-plus', color: '#ff7f00' },
  mythic: { min: 500, label: '★ MYTHIC', class: 'badge-mythic', color: '#ff66b2' },
  legendary: { min: 200, label: '★ LEGENDARY', class: 'badge-legendary', color: '#ffd700' },
  epic: { min: 140, label: '♦ EPIC', class: 'badge-epic', color: '#9b5cff' },
  rare: { min: 80, label: '◆ RARE', class: 'badge-rare', color: '#39a1ff' },
  common: { min: 40, label: 'COMMON', class: 'badge-none', color: '#808080' }
};
var SYNERGY_EMOJI_MAP = {
  'Bracelet': '⌚️',
  'Logos': '👑',
  'Earrings': '💍',
  'Color': '🎨',
  'Weapon': '⚔️',
  'Pattern': '🔄',
  'Style': '✨',
  'Emotion': '😊',
  'Skin': '👤',
  'Tribe': '🏘️',
  'Power': '⚡',
  'Magic': '🔮',
  'Element': '🌊'
};
var TEAM_SYNERGY_TRAITS = {
  logo: 'Logos',
  bracelet: 'Bracelet',
  earrings: 'Earrings'
};
function getRarityColor(score) {
  for (var key in RARITY_TIERS) {
    var tier = RARITY_TIERS[key];
    if (score >= tier.min) return tier.color;
  }
  return RARITY_TIERS.common.color;
}
function getRarityTier(score) {
  for (var key in RARITY_TIERS) {
    var tier = RARITY_TIERS[key];
    if (score >= tier.min) return tier;
  }
  return RARITY_TIERS.common;
}
function hashString(str) {
  var hash = 0;
  for (var i = 0; i < str.length; i++) {
    var char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}
function getWalletColorClass(walletAddress) {
  var hash = hashString(walletAddress || 'unknown');
  var colorIndex = hash % WALLET_COLORS.length;
  return WALLET_COLORS[colorIndex];
}
function createStickerCard(sticker, callbacks) {
  callbacks = callbacks || {};
  // normalize sticker input (may be string address or null)
  if (!sticker) sticker = {};
  if (typeof sticker === 'string') {
    sticker = { address: sticker };
  }
  var card = document.createElement('div');
  card.className = 'sticker-card';
  card.style.minHeight = '420px';  // увеличено для всех строк
  var score = Math.round(sticker.score || 0);
  var rarityTier = getRarityTier(score);
  var color = rarityTier.color;
  var badge = document.createElement('div');
  badge.className = 'sticker-badge ' + rarityTier.class;
  badge.textContent = rarityTier.label;
  card.appendChild(badge);

  var basketBtn = document.createElement('button');
  basketBtn.className = 'basket-btn';
  basketBtn.dataset.stickerAddress = sticker.address;
  var inBasket = callbacks.isInBasket ? callbacks.isInBasket(sticker.address) : false;
  basketBtn.textContent = inBasket ? '✓' : '+';
  if (inBasket) basketBtn.classList.add('active');
  basketBtn.addEventListener('click', function(e) {
    e.preventDefault();
    if (callbacks.onBasketToggle) {
      callbacks.onBasketToggle(sticker, basketBtn);
    }
  });
  card.appendChild(basketBtn);
  var img;
  var url = sticker.image_url || '';
  // caching blobs to avoid repeated downloads
  window._imageBlobCache = window._imageBlobCache || {};
  if (url && window._imageBlobCache[url]) {
    img = document.createElement('img');
    img.src = window._imageBlobCache[url];
  } else {
    img = document.createElement('img');
    img.loading = 'lazy';
    img.decoding = 'async';
    if (url) {
      // if the image lives on another host, skip fetch to avoid CORS
      try {
        const link = document.createElement('a');
        link.href = url;
        if (link.host !== window.location.host) {
          // cross-origin; assign directly and rely on browser caching
          img.src = url;
        } else {
          // same origin: fetch and cache blob
          fetch(url)
            .then(r => r.blob())
            .then(b => {
              try {
                var obj = URL.createObjectURL(b);
                window._imageBlobCache[url] = obj;
                img.src = obj;
              } catch (e) {
                img.src = url;
              }
            })
            .catch(() => { img.src = url; });
        }
      } catch (e) {
        img.src = url;
      }
    } else {
      img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=';
    }
  }
  // make sure broken images don't keep trying
  img.onerror = () => {
    img.onerror = null;
    img.src = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=';
  };
  img.alt = sticker.name || sticker.address || '';
  card.appendChild(img);
  var emotion = document.createElement('div');
  emotion.className = 'emotion-tag';
  emotion.textContent = (sticker.emotion || 'NEUTRAL').toUpperCase();
  card.appendChild(emotion);
  var title = document.createElement('div');
  title.className = 'sticker-title';
  title.textContent = sticker.name || sticker.address || 'Unknown';
  card.appendChild(title);
  var val = document.createElement('div');
  val.className = 'sticker-value';
  var a = Math.round(sticker.attr_value || 0);
  var s = Math.round(sticker.synergy_bonus || 0);
  var n = Math.round(sticker.name_value || 0);
  var aHtml = '<span style="color:' + (a > 0 ? color : '#9be7ff') + '">⚔️ ' + a + '</span>';
  var sHtml = '<span style="color:' + (s > 0 ? color : '#9be7ff') + '">🔗 ' + s + '</span>';
  var nHtml = '<span style="color:' + (n > 0 ? color : '#9be7ff') + '">⭐ ' + n + '</span>';
  val.innerHTML = '<div class="sticker-value-main">💰 ' + score + ' PWR</div><div style="font-size:11px;color:#9be7ff;margin-top:4px;">' + aHtml + ' | ' + sHtml + ' | ' + nHtml + '</div>';
  card.appendChild(val);
  
  // Display synergies as labels (like rarity badges) if available (унифицировано с корзиной)
  if (Array.isArray(sticker.synergies) && sticker.synergies.length > 0) {
    var synergiesContainer = document.createElement('div');
    synergiesContainer.style.cssText = 'display:flex;flex-direction:column;gap:2px;margin-top:4px;';
    sticker.synergies.forEach(function(syn) {
      var maxRow = syn.max_row_count || 4;
      var labelColor;
      if (maxRow === 4) labelColor = '#39a1ff';
      else if (maxRow === 5) labelColor = '#9b5cff';
      else if (maxRow === 6) labelColor = '#ffd700';
      else if (maxRow === 7) labelColor = '#ff66b2';
      else labelColor = '#808080';
      var emoji = (typeof SYNERGY_EMOJI_MAP !== 'undefined' && SYNERGY_EMOJI_MAP[syn.group_name]) ? SYNERGY_EMOJI_MAP[syn.group_name] : (syn.emoji || '✨');
      var attrValue = syn.attr_value || 'N/A';
      var label = document.createElement('div');
      label.className = 'synergy-badge';
      label.style.background = 'linear-gradient(135deg, ' + labelColor + ' 0%, ' + labelColor + ' 100%)';
      label.style.borderColor = labelColor;
      label.style.fontSize = '10px';
      label.textContent = emoji + ' ' + attrValue;
      label.title = (syn.group_name || 'Unknown') + ': ' + attrValue + ' (' + maxRow + ' атрибутов)';
      synergiesContainer.appendChild(label);
    });
    card.appendChild(synergiesContainer);
  }
  
  return card;
}

// Helper function to convert hex to RGB
function hexToRgb(hex) {
  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (result) {
    var r = parseInt(result[1], 16);
    var g = parseInt(result[2], 16);
    var b = parseInt(result[3], 16);
    return r + ',' + g + ',' + b;
  }
  return '128,128,128';  // Gray default
}

// ===============================
// SECTION: utils.js
// ===============================
/**
 * utils.js — Shared utility functions
 * (originally in utils.js)
 */
function computeTeamSynergy(team_stickers, collectionSynergy) {
  if (!collectionSynergy || !collectionSynergy.bonus_table) {
    console.warn('computeTeamSynergy: missing collectionSynergy or bonus_table');
    return { logo: 0, bracelet: 0, earrings: 0, total: 0 };
  }
  if (!Array.isArray(team_stickers)) {
    if (team_stickers && typeof team_stickers === 'object') {
      team_stickers = Object.values(team_stickers);
    } else {
      team_stickers = [];
    }
  }
  var synergyBonuses = {1:0,2:0,3:0,4:400,5:500,6:700,7:1000};
  var result = { logo: 0, bracelet: 0, earrings: 0, total: 0 };
  Object.entries(TEAM_SYNERGY_TRAITS).forEach(function([key, trait]) {
    var counts = {};
    team_stickers.forEach(function(st) {
      var attrs = st.attributes || {};
      Object.entries(attrs).forEach(function([tName, tVal]) {
        if (!tName) return;
        var match = false;
        if (key === 'logo') {
          match = tName.toLowerCase().includes('logo');
        } else {
          match = tName.toLowerCase() === trait.toLowerCase();
        }
        if (!match) return;
        var values = Array.isArray(tVal) ? tVal : [tVal];
        values.forEach(function(v) {
          if (!v) return;
          var normalizedV = String(v).trim();
          if (key === 'logo') {
            var words = normalizedV.split(/\s+/);
            if (words.length > 1) normalizedV = words[words.length - 1];
          }
          counts[normalizedV] = (counts[normalizedV] || 0) + 1;
        });
      });
    });
    var maxCount = 0;
    var maxValue = null;
    Object.entries(counts).forEach(function([val, c]) {
      if (c > maxCount) {
        maxCount = c;
        maxValue = val;
      }
    });
    maxCount = Math.min(maxCount, 7);
    var bonus = synergyBonuses[maxCount] || 0;
    result[key] = bonus;
    result.total += bonus;
    result[key + 'Count'] = maxCount;
    if (maxValue !== null) result[key + 'Value'] = maxValue;
  });
  return result;
}
function buildFilterParams(selectedSkin, selectedGroup) {
  var params = [];
  if (selectedSkin && selectedSkin !== 'ALL') params.push('skin_tone=' + encodeURIComponent(selectedSkin));
  if (selectedGroup && selectedGroup !== 'ALL') params.push('attribute_group=' + encodeURIComponent(selectedGroup));
  return params;
}

// ===============================
// SECTION: main.js
// ===============================
/**
 * main.js — Application entry point
 * (originally in main.js)
 */
// ...main.js code...

// ===============================
// SECTION: modules/ui.js
// ===============================
/**
// ===============================
// SECTION: state.js
// ===============================
function createAppState() {
  return {
    selectedSkin: null,
    selectedGroup: null,
    selectedPortfolioSkin: null,
    walletsInDb: [],
    currentSynergies: null,
    basket: new Map(),
    skinsList: []
  };
}
function createExchangeState() {
  return {
    wallets: [],
    pool: []
  };
}
function createPortfolioState() {
  return {
    lastStickerResults: [],
    currentWalletIndex: 0,
    adjustments: {}
  };
}
// ===============================
// SECTION: basket.js
// ===============================
/**
 * basket.js — Basket management and exchange distribution logic
 * (originally в basket.js)
 */
// placeholder image used across modules; keep in sync with config.createStickerCard
const PLACEHOLDER_IMAGE = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=';

// Импортируемые функции и переменные должны быть определены выше (helpers, renderBasketGroup, saveBasketToStorage и др.)
// Ниже приведён реальный код функций basket.js без экспортов:

function addToBasketSimple(stickerData, basket, callbacks) {
  callbacks = callbacks || {};
  stickerData.skin_tone = stickerData.skin_tone || stickerData.skin || stickerData.skinTone || 'Unknown';
  stickerData.owner = stickerData.wallet_address;
  stickerData.recipient = stickerData.recipient || null;
  basket.set(stickerData.address, stickerData);
  saveBasketToStorage({ basket: basket });
  if (callbacks.updateBasketBtn) callbacks.updateBasketBtn(stickerData.address, true);
  if (callbacks.onUpdated) callbacks.onUpdated();
}
function removeFromBasketSimple(stickerAddress, basket, callbacks) {
  callbacks = callbacks || {};
  basket.delete(stickerAddress);
  saveBasketToStorage({ basket: basket });
  if (callbacks.updateBasketBtn) callbacks.updateBasketBtn(stickerAddress, false);
  if (callbacks.onUpdated) callbacks.onUpdated();
}
function toggleBasketSimple(stickerAddress, stickerData, basket, callbacks) {
  callbacks = callbacks || {};
  if (basket.has(stickerAddress)) {
    removeFromBasketSimple(stickerAddress, basket, callbacks);
  } else {
    addToBasketSimple(stickerData, basket, callbacks);
  }
}
async function addToBasket(stickerData, appState, portfolioState, exchangeState, exchangeMapping, callbacks) {
  callbacks = callbacks || {};
  stickerData.skin_tone = stickerData.skin_tone || stickerData.skin || stickerData.skinTone || 'Unknown';
  stickerData.owner = stickerData.wallet_address;
  stickerData.recipient = stickerData.recipient || null;
  stickerData.attributes = stickerData.attributes || {};
  try {
    await apiAddSticker(stickerData);
  } catch (err) {
    ui.showMessage('Failed to add sticker: ' + err.message, 'error');
    console.error('apiAddSticker error', err);
    return;
  }
  appState.basket.set(stickerData.address, stickerData);
  saveBasketToStorage(appState);
  if (callbacks.rebuildExchange) callbacks.rebuildExchange();
  if (callbacks.onBasketUpdated) callbacks.onBasketUpdated();
  if (callbacks.updateExchangeBaskets) callbacks.updateExchangeBaskets();
  helpers.adjustPortfolio(stickerData.wallet_address, stickerData.skin_tone, -(stickerData.score || 0), portfolioState);
  if (callbacks.updatePortfolioIfActive) callbacks.updatePortfolioIfActive();
}
async function removeFromBasket(stickerAddress, appState, portfolioState, exchangeState, exchangeMapping, callbacks) {
  callbacks = callbacks || {};
  try {
    await apiDeleteSticker(stickerAddress);
  } catch (err) {
    ui.showMessage('Failed to remove sticker: ' + err.message, 'error');
    console.error('apiDeleteSticker error', err);
    return;
  }
  var stickerData = appState.basket.get(stickerAddress);
  appState.basket.delete(stickerAddress);
  saveBasketToStorage(appState);
  if (callbacks.rebuildExchange) callbacks.rebuildExchange();
  if (callbacks.onBasketUpdated) callbacks.onBasketUpdated();
  if (callbacks.updateExchangeBaskets) callbacks.updateExchangeBaskets();
  if (stickerData) {
    var rec = exchangeMapping[stickerAddress];
    var dest = stickerData.wallet_address;
    if (rec && rec.currentBucket && rec.currentBucket !== 'pool') dest = rec.currentBucket;
    helpers.adjustPortfolio(dest, stickerData.skin_tone, stickerData.score || 0, portfolioState);
  }
  if (callbacks.rebuildExchange) callbacks.rebuildExchange();
  if (callbacks.updatePortfolioIfActive) callbacks.updatePortfolioIfActive();
}
function updateExchangeBaskets(appState, portfolioState, exchangeState, domElements) {
  domElements = domElements || {};
  try {
    var container = document.getElementById('exchange-baskets-container');
    if (!container) return;
    container.innerHTML = '';
    var byRecipient = {};
    appState.basket.forEach(function(sticker) {
      var recipient = sticker.recipient || sticker.owner || 'Нераспределено';
      if (!byRecipient[recipient]) byRecipient[recipient] = [];
      byRecipient[recipient].push(sticker);
    });
    if (appState.basket.size === 0) {
      var msg = document.createElement('div');
      msg.className = 'info-message';
      msg.textContent = 'В корзине нет стикеров для распределения.';
      container.appendChild(msg);
      return;
    }
    // Render exchange stats table
    renderExchangeStats(container, appState);
    var recipients = Object.keys(byRecipient).sort();
    recipients.forEach(function(recipientAddr) {
      var stickers = byRecipient[recipientAddr];
      var label = recipientAddr === 'Нераспределено' ? '(не назначен)' : helpers.shortAddr(recipientAddr);
      renderBasketGroup(container, '👤 ' + label, stickers, {
        onRemove: function(addr) {
          if (domElements.removeFromBasketCallback) domElements.removeFromBasketCallback(addr);
        },
        onSend: function(btn, addr) {
          if (domElements.showRecipientMenuCallback) domElements.showRecipientMenuCallback(btn, addr);
        }
      });
    });
    var newPane = document.getElementById('basket-new-portfolio');
    if (newPane && newPane.classList.contains('active')) {
      if (typeof renderNewPortfolio === 'function') {
        renderNewPortfolio(appState, portfolioState, exchangeState, domElements)
          .catch(function(err) { console.error('new portfolio render failed', err); });
      }
    }
  } catch (err) {
    console.error('updateExchangeBaskets error', err);
  }
}
async function updateBasketSticker(stickerData, appState, callbacks) {
  callbacks = callbacks || {};
  if (!stickerData || !stickerData.address) return;
  try {
    await apiUpdateSticker(stickerData.address, stickerData.recipient || null);
  } catch (err) {
    ui.showMessage('Failed to update sticker: ' + err.message, 'error');
    console.error('apiUpdateSticker error', err);
    return;
  }
  appState.basket.set(stickerData.address, stickerData);
  saveBasketToStorage(appState);
  if (callbacks.updateBasketBtn) callbacks.updateBasketBtn(stickerData.address, true);
  if (callbacks.onBasketUpdated) callbacks.onBasketUpdated();
}

async function toggleBasket(stickerAddress, stickerData, appState, portfolioState, exchangeState, exchangeMapping, callbacks) {
  callbacks = callbacks || {};
  if (appState.basket.has(stickerAddress)) {
    const existing = appState.basket.get(stickerAddress);
    if (stickerData && JSON.stringify(existing) !== JSON.stringify(stickerData)) {
      // Sticker metadata changed (recipient update)
      await updateBasketSticker(stickerData, appState, callbacks);
      return;
    }
    await removeFromBasket(stickerAddress, appState, portfolioState, exchangeState, exchangeMapping, callbacks);
  } else {
    await addToBasket(stickerData, appState, portfolioState, exchangeState, exchangeMapping, callbacks);
  }
}

/**
 * Render basket statistics table with breakdown by wallets and tribes
 */
function renderBasketStats(container, appState) {
  if (!container) return;
  container.innerHTML = '';
  
  if (appState.basket.size === 0) return;
  
  // Group by wallet and tribe, counting by rarity
  const byWallet = {};
  const byWalletStickers = {};
  const allTribes = new Set();
  const rarityLabels = { unique: 'U', mythicPlus: 'M+', mythic: 'M', legendary: 'L', epic: 'E', rare: 'R', common: 'C' };
  
  appState.basket.forEach(function(sticker) {
    const wallet = sticker.wallet_address || sticker.owner || 'unknown';
    const tribe = sticker.skin_tone || 'unknown';
    const score = Math.round(sticker.score || 0);
    const rarityTier = getRarityTier(score);
    let rarityKey = 'common';
    for (var key in RARITY_TIERS) {
      if (score >= RARITY_TIERS[key].min) {
        rarityKey = key;
        break;
      }
    }

    if (!byWallet[wallet]) {
      byWallet[wallet] = { tribes: {}, total: 0, pwr: 0 };
    }
    if (!byWallet[wallet].tribes[tribe]) {
      byWallet[wallet].tribes[tribe] = { count: 0, pwr: 0, byRarity: {} };
    }

    byWallet[wallet].tribes[tribe].byRarity[rarityKey] = (byWallet[wallet].tribes[tribe].byRarity[rarityKey] || 0) + 1;
    byWallet[wallet].tribes[tribe].count += 1;
    byWallet[wallet].tribes[tribe].pwr += (sticker.score || 0);
    byWallet[wallet].total += 1;
    byWallet[wallet].pwr += (sticker.score || 0);
    allTribes.add(tribe);

    // accumulate stickers for attribute stats
    if (!byWalletStickers[wallet]) byWalletStickers[wallet] = [];
    byWalletStickers[wallet].push(sticker);
  });
  
  const wallets = Object.keys(byWallet).sort();
  const tribes = Array.from(allTribes).sort(function(a, b) {
    const sa = a.toLowerCase();
    const sb = b.toLowerCase();
    if (typeof SKIN_ORDER !== 'undefined' && Array.isArray(SKIN_ORDER)) {
      const ai = SKIN_ORDER.findIndex(x => (x||'').toString().toLowerCase() === sa);
      const bi = SKIN_ORDER.findIndex(x => (x||'').toString().toLowerCase() === sb);
      if (ai !== -1 || bi !== -1) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    }
    return a.localeCompare(b);
  });
  
  const statsTable = document.createElement('table');
  statsTable.style.cssText = 'width:auto;border-collapse:collapse;font-size:12px;margin-bottom:8px;background:rgba(30,40,50,0.8);border:1px solid #45688a;';
  
  // Header row with tribes
  const headerRow = statsTable.insertRow();
  headerRow.style.background = 'rgba(20,30,40,0.9)';
  
  const walletHeaderCell = headerRow.insertCell();
  walletHeaderCell.textContent = 'Кошелёк';
  walletHeaderCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#fbbf24;min-width:140px;';

  tribes.forEach(function(tribe) {
    const cell = headerRow.insertCell();
    cell.textContent = tribe;
    cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#39a1ff;text-align:center;min-width:120px;';
  });

  const totalHeaderCell = headerRow.insertCell();
  totalHeaderCell.textContent = 'Всего PWR';
  totalHeaderCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#39a1ff;text-align:center;min-width:120px;';

  // Wallet rows
  const totalsByTribe = {};
  let grandTotalPwr = 0;

  wallets.forEach(function(wallet) {
    const row = statsTable.insertRow();
    const walletCell = row.insertCell();
    walletCell.textContent = wallet === 'unknown' ? '(unknown)' : helpers.shortAddr(wallet);
    walletCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;';

    let walletTotalPwr = 0;
    tribes.forEach(function(tribe) {
      const cell = row.insertCell();
      const walletData = byWallet[wallet];
      const tribeData = walletData.tribes[tribe];

      if (tribeData) {
        const cellDiv = document.createElement('div');
        cellDiv.style.cssText = 'display:flex;flex-direction:column;gap:2px;';

        const rarityOrder = ['unique', 'mythicPlus', 'mythic', 'legendary', 'epic', 'rare', 'common'];
        const rarityBadgesDiv = document.createElement('div');
        rarityBadgesDiv.style.cssText = 'display:flex;flex-direction:column;gap:1px;';

        rarityOrder.forEach(function(rarity) {
          const count = tribeData.byRarity[rarity];
          if (count) {
            const rarityTier = RARITY_TIERS[rarity];
            const badge = document.createElement('div');
            badge.className = 'synergy-badge';
            badge.style.cssText = 'background:linear-gradient(135deg,' + rarityTier.color + ' 0%,' + rarityTier.color + ' 100%);border-color:' + rarityTier.color + ';font-size:10px;padding:2px 4px;';
            badge.textContent = rarityTier.label + ' x' + count;
            rarityBadgesDiv.appendChild(badge);
          }
        });
        cellDiv.appendChild(rarityBadgesDiv);

        const pwrDiv = document.createElement('div');
        pwrDiv.style.cssText = 'color:#fbbf24;font-size:11px;font-weight:bold;margin-top:2px;';
        pwrDiv.textContent = tribeData.pwr + ' 💰';
        cellDiv.appendChild(pwrDiv);

        cell.appendChild(cellDiv);

        totalsByTribe[tribe] = (totalsByTribe[tribe] || 0) + tribeData.pwr;
        walletTotalPwr += tribeData.pwr;
      } else {
        cell.textContent = '-';
        cell.style.color = '#666';
      }
      cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;font-size:12px;vertical-align:top;';
    });

    const totalCell = row.insertCell();
    totalCell.textContent = walletTotalPwr + ' 💰';
    totalCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;font-weight:bold;color:#fbbf24;';

    grandTotalPwr += walletTotalPwr;
  });

  // Totals row
  const totalRow = statsTable.insertRow();
  totalRow.style.background = 'rgba(20,30,40,0.9)';
  totalRow.style.fontWeight = 'bold';

  const totalWalletCell = totalRow.insertCell();
  totalWalletCell.textContent = 'ВСЕГО';
  totalWalletCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;color:#fbbf24;';

  tribes.forEach(function(tribe) {
    const cell = totalRow.insertCell();
    const pwr = totalsByTribe[tribe] || 0;
    cell.textContent = pwr + ' 💰';
    cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;color:#fbbf24;';
  });

  const grandTotalCell = totalRow.insertCell();
  grandTotalCell.textContent = grandTotalPwr + ' 💰';
  grandTotalCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;color:#fbbf24;';

  container.appendChild(statsTable);

  // Attribute counts for basket wallets
  const attrPriority = [
    'Bitcoin', 'ETH', 'TON', 'Telegram', 'Dollar', 'RUB', 'Zargates', 'Tribo Games', 'Elephant'
  ];
  const attrCounts = computeAttributeCountsByGroup(byWalletStickers, attrPriority);
  renderAttributeStatsTable(container, attrCounts, attrPriority);
}

/**
 * Render exchange basket statistics table with breakdown by recipients and tribes
 */
function renderExchangeStats(container, appState) {
  if (!container) return;
  
  if (appState.basket.size === 0) return;
  
  // Group by recipient and tribe, counting by rarity
  const byRecipient = {};
  const byRecipientStickers = {};
  const allTribes = new Set();
  const rarityLabels = { unique: 'U', mythicPlus: 'M+', mythic: 'M', legendary: 'L', epic: 'E', rare: 'R', common: 'C' };
  
  appState.basket.forEach(function(sticker) {
    const recipient = sticker.recipient || sticker.wallet_address || 'Нераспределено';
    const tribe = sticker.skin_tone || 'unknown';
    const score = Math.round(sticker.score || 0);
    let rarityKey = 'common';
    for (var key in RARITY_TIERS) {
      if (score >= RARITY_TIERS[key].min) {
        rarityKey = key;
        break;
      }
    }
    
    if (!byRecipient[recipient]) {
      byRecipient[recipient] = { tribes: {}, total: 0, pwr: 0 };
    }
    if (!byRecipient[recipient].tribes[tribe]) {
      byRecipient[recipient].tribes[tribe] = { count: 0, pwr: 0, byRarity: {} };
    }
    
    byRecipient[recipient].tribes[tribe].byRarity[rarityKey] = (byRecipient[recipient].tribes[tribe].byRarity[rarityKey] || 0) + 1;
    byRecipient[recipient].tribes[tribe].count += 1;
    byRecipient[recipient].tribes[tribe].pwr += (sticker.score || 0);
    byRecipient[recipient].total += 1;
    byRecipient[recipient].pwr += (sticker.score || 0);
    allTribes.add(tribe);

    if (!byRecipientStickers[recipient]) byRecipientStickers[recipient] = [];
    byRecipientStickers[recipient].push(sticker);
  });
  
  const recipients = Object.keys(byRecipient).sort();
  const tribes = Array.from(allTribes).sort(function(a, b) {
    const sa = a.toLowerCase();
    const sb = b.toLowerCase();
    if (typeof SKIN_ORDER !== 'undefined' && Array.isArray(SKIN_ORDER)) {
      const ai = SKIN_ORDER.findIndex(x => (x||'').toString().toLowerCase() === sa);
      const bi = SKIN_ORDER.findIndex(x => (x||'').toString().toLowerCase() === sb);
      if (ai !== -1 || bi !== -1) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    }
    return a.localeCompare(b);
  });
  
  const statsTable = document.createElement('table');
  statsTable.style.cssText = 'width:auto;border-collapse:collapse;font-size:12px;margin-bottom:8px;background:rgba(30,40,50,0.8);border:1px solid #45688a;';
  
  // Header row with recipient addresses
  const headerRow = statsTable.insertRow();
  headerRow.style.background = 'rgba(20,30,40,0.9)';
  
  const tribeHeaderCell = headerRow.insertCell();
  tribeHeaderCell.textContent = 'Трайб';
  tribeHeaderCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#fbbf24;min-width:100px;';
  
  recipients.forEach(function(recipient) {
    const cell = headerRow.insertCell();
    const shortRecipient = recipient === 'Нераспределено' ? '(не назначен)' : helpers.shortAddr(recipient);
    cell.textContent = shortRecipient;
    cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;color:#39a1ff;text-align:center;min-width:120px;';
  });
  
  // Tribe rows
  tribes.forEach(function(tribe) {
    const row = statsTable.insertRow();
    
    const tribeCell = row.insertCell();
    tribeCell.textContent = tribe;
    tribeCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;font-weight:bold;';
    
    recipients.forEach(function(recipient) {
      const cell = row.insertCell();
      const recipientData = byRecipient[recipient];
      const tribeData = recipientData.tribes[tribe];
      
      if (tribeData) {
        const cellDiv = document.createElement('div');
        cellDiv.style.cssText = 'display:flex;flex-direction:column;gap:2px;';
        
        // Create rarity badges
        const rarityOrder = ['unique', 'mythicPlus', 'mythic', 'legendary', 'epic', 'rare', 'common'];
        const rarityBadgesDiv = document.createElement('div');
        rarityBadgesDiv.style.cssText = 'display:flex;flex-direction:column;gap:1px;';
        
        rarityOrder.forEach(function(rarity) {
          const count = tribeData.byRarity[rarity];
          if (count) {
            const rarityTier = RARITY_TIERS[rarity];
            const badge = document.createElement('div');
            badge.className = 'synergy-badge';
            badge.style.cssText = 'background:linear-gradient(135deg,' + rarityTier.color + ' 0%,' + rarityTier.color + ' 100%);border-color:' + rarityTier.color + ';font-size:10px;padding:2px 4px;';
            badge.textContent = rarityTier.label + ':' + count;
            rarityBadgesDiv.appendChild(badge);
          }
        });
        cellDiv.appendChild(rarityBadgesDiv);
        
        const pwrDiv = document.createElement('div');
        pwrDiv.style.cssText = 'color:#fbbf24;font-size:11px;font-weight:bold;margin-top:2px;';
        pwrDiv.textContent = tribeData.pwr + ' 💰';
        cellDiv.appendChild(pwrDiv);
        
        cell.appendChild(cellDiv);
      } else {
        cell.textContent = '-';
        cell.style.color = '#666';
      }
      cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;font-size:12px;';
    });
  });
  
  // Total row
  const totalRow = statsTable.insertRow();
  totalRow.style.background = 'rgba(20,30,40,0.9)';
  totalRow.style.fontWeight = 'bold';
  
  const totalWalletCell = totalRow.insertCell();
  totalWalletCell.textContent = 'ВСЕГО';
  totalWalletCell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;color:#fbbf24;';
  
  recipients.forEach(function(recipient) {
    const cell = totalRow.insertCell();
    const recipientData = byRecipient[recipient];
    let totalByRarity = {};
    
    // Aggregate all rarities for this recipient
    Object.keys(recipientData.tribes).forEach(function(tribe) {
      const tribeData = recipientData.tribes[tribe];
      Object.keys(tribeData.byRarity).forEach(function(rarity) {
        totalByRarity[rarity] = (totalByRarity[rarity] || 0) + tribeData.byRarity[rarity];
      });
    });
    
    const cellDiv = document.createElement('div');
    cellDiv.style.cssText = 'display:flex;flex-direction:column;gap:2px;';
    
    const rarityBadgesDiv = document.createElement('div');
    rarityBadgesDiv.style.cssText = 'display:flex;flex-direction:column;gap:1px;';
    
    const rarityOrder = ['unique', 'mythicPlus', 'mythic', 'legendary', 'epic', 'rare', 'common'];
    rarityOrder.forEach(function(rarity) {
      const count = totalByRarity[rarity];
      if (count) {
        const rarityTier = RARITY_TIERS[rarity];
        const badge = document.createElement('div');
        badge.className = 'synergy-badge';
        badge.style.cssText = 'background:linear-gradient(135deg,' + rarityTier.color + ' 0%,' + rarityTier.color + ' 100%);border-color:' + rarityTier.color + ';font-size:10px;padding:2px 4px;';
        badge.textContent = rarityTier.label + ':' + count;
        rarityBadgesDiv.appendChild(badge);
      }
    });
    cellDiv.appendChild(rarityBadgesDiv);
    
    const pwrDiv = document.createElement('div');
    pwrDiv.style.cssText = 'color:#fbbf24;font-size:11px;font-weight:bold;margin-top:2px;';
    pwrDiv.textContent = recipientData.pwr + ' 💰';
    cellDiv.appendChild(pwrDiv);
    
    cell.appendChild(cellDiv);
    cell.style.cssText = 'padding:6px 8px;border:1px solid #45688a;text-align:center;color:#fbbf24;font-weight:bold;font-size:12px;';
  });
  
  container.appendChild(statsTable);

  // Attribute counts for exchange recipients
  const attrPriority = [
    'Bitcoin', 'ETH', 'TON', 'Telegram', 'Dollar', 'RUB', 'Zargates', 'Tribo Games', 'Elephant'
  ];
  const attrCounts = computeAttributeCountsByGroup(byRecipientStickers, attrPriority);
  renderAttributeStatsTable(container, attrCounts, attrPriority);
}

function updateOriginalBaskets(appState, domElements) {
  domElements = domElements || {};
  try {
    var container = document.getElementById('basket-items');
    var emptyMsg = document.getElementById('basket-empty');
    var contentElem = domElements.basketContent || document.getElementById('basket-content');
    var statsContainer = document.getElementById('basket-stats');
    if (!container) return;
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '12px';
    if (emptyMsg) emptyMsg.style.display = appState.basket.size === 0 ? 'block' : 'none';
    if (contentElem) contentElem.style.display = appState.basket.size === 0 ? 'none' : 'block';
    // Render basket stats
    if (statsContainer) renderBasketStats(statsContainer, appState);
    var byWallet = {};
    appState.basket.forEach(function(sticker) {
      var orig = sticker.wallet_address || sticker.owner || 'unknown';
      if (!byWallet[orig]) byWallet[orig] = [];
      byWallet[orig].push(sticker);
    });
    if (appState.basket.size === 0) return;
    var wallets = Object.keys(byWallet).sort();
    wallets.forEach(function(walletAddr) {
      var label = walletAddr === 'unknown' ? '(unknown)' : helpers.shortAddr(walletAddr);
      renderBasketGroup(container, '💼 ' + label, byWallet[walletAddr], {
        onRemove: function(addr) {
          if (domElements.removeFromBasketCallback) domElements.removeFromBasketCallback(addr);
        },
        onSend: function(btn, addr) {
          if (domElements.showRecipientMenuCallback) domElements.showRecipientMenuCallback(btn, addr);
        }
      });
    });
  } catch (err) {
    console.error('updateOriginalBaskets error', err);
  }
}

// renderNewPortfolio (from basket.js)
async function renderNewPortfolio(appState, portfolioState, exchangeState, domElements = {}) {
  var container = document.getElementById('basket-new-portfolio');
  if (!container) return;
  container.innerHTML = '';

  var originalResults = portfolioState.lastStickerResults || [];
  var basketList = Array.from(appState.basket.values());

  var newResults = [];
  if ((exchangeState.wallets || []).length > 0) {
    container.innerHTML = '<p class="info-message">Загрузка новых портфелей...</p>';
    try {
      var fetched = await Promise.all(
        exchangeState.wallets.map(async function(w) {
          var addr = w.address;
          if (!addr) return null;
          var useBasket = basketList.length > 0;
          if (!addr || addr === 'unknown') {
            console.warn('skipping optimal-teams fetch for invalid wallet address', addr);
            return { teamsResp: {teams:{}}, stickersResp: {stickers:[]} };
          }
          var [teamsResp, stickersResp] = await Promise.all([
            api.fetchOptimalTeams ? api.fetchOptimalTeams(addr, basketList.length > 0 ? true : false) : Promise.resolve({teams:{}}),
            api.fetchWalletStickers(addr, basketList.length > 0 ? true : null)
          ]);
          return { teamsResp: teamsResp, stickersResp: stickersResp };
        })
      );
      newResults = fetched.filter(r => r && r.teamsResp).map(function(r) {
        var resp = r.teamsResp;
        var orig = originalResults.find(function(x) {
          return (x.wallet || x.address) === (resp.wallet || resp.address);
        }) || {};
        return {
          wallet: resp.wallet || resp.address,
          address: resp.wallet || resp.address,
          teams: resp.teams || {},
          stickers: (r.stickersResp && r.stickersResp.stickers) || [],
          collection_synergy: resp.collection_synergy || orig.collection_synergy || null,
          orig_teams: orig.teams || [],
          orig_stickers: orig.stickers || []
        };
      });
    } catch (err) {
      console.error('failed to fetch new portfolio data', err);
      newResults = (exchangeState.wallets || []).map(function(w) {
        var orig = originalResults.find(function(x) {
          return (x.wallet || x.address) === w.address;
        }) || {};
        return {
          wallet: w.address,
          address: w.address,
          teams: {},
          stickers: [],
          collection_synergy: orig.collection_synergy || null,
          orig_teams: orig.teams || [],
          orig_stickers: orig.stickers || []
        };
      });
    }
  }

  if (newResults.length === 0) {
    container.innerHTML = '<p class="info-message">Корзина пуста — нет данных для нового портфеля.</p>';
    return;
  }

  // create a dedicated stats container inside the new‑portfolio pane
  const statsDiv = document.createElement('div');
  // use the same class as the original stats container for consistent styling
  statsDiv.className = 'wallet-stats';
  statsDiv.style.marginBottom = '12px';
  // optional id for easier debugging
  statsDiv.id = 'new-portfolio-stats';
  container.appendChild(statsDiv);

  // show same stats table as in portfolio tab but using newResults
  console.log('DEBUG: newResults for stats table:', newResults);
  if (newResults.length > 0) {
    console.log('DEBUG: first newResult stickers:', newResults[0].stickers);
    if (newResults[0].stickers && newResults[0].stickers.length > 0) {
      console.log('DEBUG: first sticker attributes:', newResults[0].stickers[0].attributes);
    }
  }
  renderPortfolioStatsTable(newResults, appState, portfolioState, { portfolioStats: statsDiv });

  // also render the sticker view beneath (optional, similar to portfolio)
  const detailsSelector = document.createElement('div');
  detailsSelector.className = 'wallet-selector';
  const detailsContent = document.createElement('div');
  detailsContent.className = 'portfolio-content';
  container.appendChild(detailsSelector);
  container.appendChild(detailsContent);
  const subDom = { walletSelector: detailsSelector, portfolioSection: detailsContent, portfolioStats: statsDiv };
  renderWalletSelector(newResults, appState, portfolioState, subDom);
  renderPortfolio(0, newResults, appState, portfolioState, subDom);
}


function isInBasket(stickerAddress, appState) {
  return appState.basket.has(stickerAddress);
}

// helper definitions; rebuildExchangeStateFromBasket implemented further down

function rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping) {
  var walletsMap = {};
  (appState.walletsInDb || []).forEach(function(w) {
    walletsMap[w.address] = { stickers: [], originalPower: 0, currentPower: 0 };
  });
  appState.basket.forEach(function(st) {
    var orig = st.wallet_address || 'unknown';
    // skip items where wallet address is unknown; they can't participate in exchanges
    if (orig === 'unknown') {
      console.debug('rebuildExchangeState skipping sticker with unknown wallet', st);
      return;
    }
    if (!walletsMap[orig]) walletsMap[orig] = { stickers: [], originalPower: 0, currentPower: 0 };
    walletsMap[orig].stickers.push(st);
    walletsMap[orig].originalPower += st.score || 0;
    walletsMap[orig].currentPower += st.score || 0;
  });
  exchangeState.wallets = Object.entries(walletsMap).map(function([addr, obj]) {
    return {
      address: addr,
      stickers: [],
      originalPower: obj.originalPower,
      currentPower: obj.currentPower
    };
  });
  exchangeState.pool = Array.from(appState.basket.values());
  var newMapping = {};
  exchangeState.pool.forEach(function(st) {
    if (exchangeMapping[st.id]) {
      newMapping[st.id] = {
        originalWallet: exchangeMapping[st.id].originalWallet,
        currentBucket: exchangeMapping[st.id].currentBucket,
        sticker: st
      };
    } else {
      newMapping[st.id] = {
        originalWallet: st.wallet_address,
        currentBucket: 'pool',
        sticker: st
      };
    }
  });
  exchangeState.wallets.forEach(function(w) {
    w.stickers = [];
  });
  Object.values(newMapping).forEach(function(rec) {
    if (rec.currentBucket && rec.currentBucket !== 'pool') {
      var w = exchangeState.wallets.find(function(w) { return w.address === rec.currentBucket; });
      if (w) {
        w.stickers.push(rec.sticker);
        w.currentPower += rec.sticker.score || 0;
      }
    }
  });
  exchangeState.wallets.forEach(function(w) {
    w.currentPower = recalcWalletPower(w.stickers);
  });
  exchangeMapping = newMapping;
  updateExchangeBaskets(appState, portfolioState, exchangeState);
}

// expose basket functions to global object
basket.addToBasketSimple = addToBasketSimple;
basket.removeFromBasketSimple = removeFromBasketSimple;
basket.toggleBasketSimple = toggleBasketSimple;
// allow callers to refresh sticker data without triggering removal/add
basket.updateBasketSticker = updateBasketSticker;
basket.addToBasket = addToBasket;
basket.removeFromBasket = removeFromBasket;
basket.toggleBasket = toggleBasket;
basket.updateExchangeBaskets = updateExchangeBaskets;
basket.updateOriginalBaskets = updateOriginalBaskets;
basket.renderNewPortfolio = renderNewPortfolio;
basket.isInBasket = isInBasket;
basket.rebuildExchangeStateFromBasket = rebuildExchangeStateFromBasket;
// (ui.js already defined earlier in file for early initialization)

// ===============================
// SECTION: modules/portfolio.js
// ===============================
/**
 * modules/portfolio.js — Portfolio tab logic
 * (originally в modules/portfolio.js)
 */
// dependencies: helpers, stats, render, api, basket, WALLET_COLORS, EMOTION_ORDER, SKIN_ORDER

function renderPortfolio(walletIndex, walletResults, appState, portfolioState, domElements) {
  if (!domElements.portfolioSection) return;
  const wallet = walletResults[walletIndex];
  if (!wallet) return;
  const walletAddress = wallet.wallet || wallet.address || '';
  const { stickers = [] } = wallet;
  portfolioState.currentWalletIndex = walletIndex;
  portfolioState.lastStickerResults = walletResults;
  domElements.portfolioSection.innerHTML = '';

  // Skin filter controls
  const filterDiv = document.createElement('div');
  filterDiv.style.marginBottom = '12px';
  filterDiv.style.display = 'flex';
  filterDiv.style.flexWrap = 'wrap';
  filterDiv.style.gap = '6px';
  const skins = ['Все'].concat(SKIN_ORDER);
  skins.forEach(skin => {
    const btn = document.createElement('button');
    btn.className = 'tab-btn';
    btn.textContent = skin;
    if ((skin === 'Все' && !portfolioState.selectedPortfolioSkin) || portfolioState.selectedPortfolioSkin === skin) {
      btn.classList.add('active');
    }
    btn.addEventListener('click', () => {
      portfolioState.selectedPortfolioSkin = (skin === 'Все' ? null : skin);
      renderPortfolio(walletIndex, walletResults, appState, portfolioState, domElements);
    });
    filterDiv.appendChild(btn);
  });
  domElements.portfolioSection.appendChild(filterDiv);

  // Filter stickers by skin
  const filterSkin = portfolioState.selectedPortfolioSkin || null;
  let filteredStickers = stickers;
  if (filterSkin) {
    filteredStickers = stickers.filter(s => (s.skin_tone || 'Unknown') === filterSkin);
  }

  // Group by skin tone
  const bySkin = {};
  filteredStickers.forEach(s => {
    const skin = s.skin_tone || 'Unknown';
    if (!bySkin[skin]) bySkin[skin] = [];
    bySkin[skin].push(s);
  });
  const skinOrder = SKIN_ORDER.filter(sk => bySkin[sk]).concat(
    Object.keys(bySkin).filter(sk => !SKIN_ORDER.includes(sk))
  );

  // Render each skin group
  skinOrder.forEach(skin => {
    const skinStickers = bySkin[skin] || [];
    // compute stats for this skin (base sticker power + team bonuses)
    let skinStats;
    if (wallet.teams && wallet.teams[skin] && wallet.teams[skin].length) {
      skinStats = stats.computePortfolioStats(
        skinStickers,
        skin,
        wallet.collection_synergy || null,
        wallet.teams[skin]
      );
    } else {
      skinStats = stats.computePortfolioStats(skinStickers, skin, wallet.collection_synergy || null);
    }
    let powerSum = skinStats.totalPower;
    let teams = [];
    const teamCount = skinStats.teamCount;
    const fullCount = skinStats.fullCount;

    // for leftover rendering we may need these maps even if API teams were used
    let emotionMap = {};
    let usedIndices = {};

    // prepare display teams array: either API-provided or greedy-built
    if (wallet.teams && wallet.teams[skin] && wallet.teams[skin].length) {
      teams = wallet.teams[skin].map(t => ({
        emotions: t.emotions || [],
        stickers: t.stickers || [],
        isComplete: !!t.is_complete || !!t.isComplete,
        total_pwr: t.total_pwr != null ? t.total_pwr : (Array.isArray(t.stickers) ? t.stickers.reduce((s,st)=>s+(st.score||0),0) : 0)
      }));
    } else {
      // fallback to client-side greedy assembly
      emotionMap = {};
      skinStickers.forEach(s => {
        const e = s.emotion || 'NEUTRAL';
        if (!emotionMap[e]) emotionMap[e] = [];
        emotionMap[e].push(s);
      });
      Object.keys(emotionMap).forEach(e => {
        emotionMap[e].sort((a,b)=> (b.score||0)-(a.score||0));
      });
      usedIndices = {};
      Object.keys(emotionMap).forEach(e=>usedIndices[e]=0);
      while (true) {
        const available = Object.keys(emotionMap).filter(e=>usedIndices[e]<emotionMap[e].length);
        if (available.length===0) break;
        const scored = available.map(e=>({emotion:e,power:(emotionMap[e][usedIndices[e]]&&emotionMap[e][usedIndices[e]].score)||0}))
                          .sort((a,b)=>b.power-a.power);
        const selected = scored.slice(0,7).map(s=>s.emotion);
        const teamStickers = [];
        selected.forEach(em=>{
          const st = emotionMap[em][usedIndices[em]];
          if (st) { teamStickers.push(st); usedIndices[em]++; }
        });
        if (teamStickers.length>0) teams.push({emotions:selected,stickers:teamStickers,isComplete:selected.length===7&&teamStickers.length===7}); else break;
      }
    }

    const skinSection = document.createElement('div');
    skinSection.style.marginBottom = '24px';
    const skinHeader = document.createElement('div');
    skinHeader.style.fontSize = '14px';
    skinHeader.style.fontWeight = '700';
    skinHeader.style.color = '#9be7ff';
    skinHeader.style.marginBottom = '12px';
    skinHeader.textContent = `🎨 ${skin} — ${skinStickers.length} стикеров, ${teamCount} команд, ${fullCount} полных, ${powerSum} PWR`;
    // optionally show breakdown in title
    skinHeader.title = `stickers:${skinStats.stickerPower} · synergy:${skinStats.synergyPower} · teams:${skinStats.teamPower}`;
    skinSection.appendChild(skinHeader);

    teams.sort((a, b) => {
      const pwrA = a.total_pwr != null ? a.total_pwr : a.stickers.reduce((s, st) => s + (st.score || 0), 0);
      const pwrB = b.total_pwr != null ? b.total_pwr : b.stickers.reduce((s, st) => s + (st.score || 0), 0);
      return pwrB - pwrA;
    });
    teams.forEach((team, idx) => {
      renderTeam(skinSection, team, idx + 1, EMOTION_ORDER, team.isComplete, appState, wallet.collection_synergy);
    });
    // Render any remaining stickers as individual teams (fallback)
    if (Object.keys(emotionMap).length > 0) {
      let nextIdx = teams.length + 1;
      Object.keys(emotionMap).forEach(e => {
        const remaining = emotionMap[e].slice(usedIndices[e] || 0);
        remaining.forEach(st => {
          const team = { emotions: [st.emotion], stickers: [st], isComplete: false };
          renderTeam(skinSection, team, nextIdx++, EMOTION_ORDER, false, appState, wallet.collection_synergy);
        });
      });
    }
    domElements.portfolioSection.appendChild(skinSection);
  });
}

function renderTeam(container, team, teamIdx, emotionOrder, isComplete, appState, collectionSynergy = null) {
  if (!appState) {
    console.warn('[portfolio.renderTeam] appState is undefined!');
    return;
  }
  if (!appState.basket) {
    console.warn('[portfolio.renderTeam] appState.basket is undefined!');
    return;
  }

  const teamDiv = document.createElement('div');
  teamDiv.style.marginBottom = '12px';
  teamDiv.style.padding = '12px';
  teamDiv.style.background = 'linear-gradient(135deg, #1a2332 0%, #0f1419 100%)';
  teamDiv.style.borderRadius = '8px';
  teamDiv.style.border = '1px solid rgba(77, 184, 255, 0.15)';

  // breakdown of components (attr/name/individual & team synergies)
  const teamAttr = team.stickers.reduce((s, st) => s + (st.attr_value || 0), 0);
  const teamName = team.stickers.reduce((s, st) => s + (st.name_value || 0), 0);
  const individualSynergy = team.stickers.reduce((s, st) => s + (st.synergy_bonus || 0), 0);
  const teamSynObj = stats.computeTeamSynergy(team.stickers || [], collectionSynergy);
  const teamLevelSyn = teamSynObj.total || 0;
  const logo = teamSynObj.logo || 0;
  const bracelet = teamSynObj.bracelet || 0;
  const earrings = teamSynObj.earrings || 0;
  const logoVal = teamSynObj.logoValue || '';
  const braceletVal = teamSynObj.braceletValue || '';
  const earringsVal = teamSynObj.earringsValue || '';

  const bonus = isComplete ? 350 : 0;
  const total = Math.round(teamAttr + individualSynergy + teamLevelSyn + teamName + bonus);

  const teamHeader = document.createElement('div');
  teamHeader.style.display = 'flex';
  teamHeader.style.justifyContent = 'space-between';
  teamHeader.style.alignItems = 'center';
  teamHeader.style.marginBottom = '12px';
  teamHeader.style.gap = '8px';

  const headerLeft = document.createElement('div');
  headerLeft.style.display = 'flex';
  headerLeft.style.gap = '8px';
  headerLeft.style.alignItems = 'center';

  const badge = document.createElement('span');
  badge.style.fontSize = '10px';
  badge.style.fontWeight = '700';
  badge.style.color = '#000';
  badge.style.background = isComplete ? '#fbbf24' : '#64748b';
  badge.style.padding = '4px 8px';
  badge.style.borderRadius = '4px';
  badge.textContent = isComplete ? 'FULL TEAM' : `${team.emotions.length}/7`;

  const label = document.createElement('span');
  label.style.color = '#9be7ff';
  label.style.fontWeight = '700';
  label.style.fontSize = '12px';
  label.textContent = `Команда ${teamIdx}`;

  // breakdown display similar to legacy app.js
  const breakdown = document.createElement('div');
  breakdown.style.display = 'flex';
  breakdown.style.gap = '12px';
  breakdown.style.marginTop = '8px';

  const teamColor = getRarityColor(total);
  const compA = document.createElement('div');
  compA.style.color = teamAttr > 0 ? teamColor : '#9be7ff';
  compA.textContent = `⚔️ ${Math.round(teamAttr)}`;

  const compS = document.createElement('div');
  compS.style.color = individualSynergy > 0 ? teamColor : '#9be7ff';
  compS.textContent = `🔗 ${Math.round(individualSynergy)}`;

  const compSD = document.createElement('div');
  compSD.style.color = (logo > 0 || bracelet > 0 || earrings > 0) ? teamColor : '#9be7ff';
  const detailParts = [];
  if (logo > 0) detailParts.push(`👑 ${logoVal || 'Logo'}: ${logo}`);
  if (bracelet > 0) detailParts.push(`💎 ${braceletVal || 'Bracelet'}: ${bracelet}`);
  if (earrings > 0) detailParts.push(`💍 ${earringsVal || 'Earrings'}: ${earrings}`);
  if (collectionSynergy && collectionSynergy.bonus_table && Array.isArray(team.stickers)) {
      const themeCounts = {};
      team.stickers.forEach(st => {
          (st.themes || []).forEach(t => themeCounts[t] = (themeCounts[t] || 0) + 1);
      });
      Object.entries(themeCounts).forEach(([t, c]) => {
          const key = c >= 3 ? '3+' : String(c);
          const tb = collectionSynergy.bonus_table[key] || 0;
          if (tb > 0) {
              detailParts.push(`🧩 ${t}: ${tb}`);
          }
      });
  }
  if (detailParts.length) compSD.textContent = detailParts.join(' · ');

  const compN = document.createElement('div');
  compN.style.color = teamName > 0 ? teamColor : '#9be7ff';
  compN.textContent = `⭐ ${Math.round(teamName)}`;
  const compB = document.createElement('div');
  compB.style.color = bonus > 0 ? '#fbbf24' : '#9be7ff';
  compB.textContent = `🎁 ${bonus}`;

  breakdown.appendChild(compA);
  breakdown.appendChild(compS);
  if (detailParts.length) breakdown.appendChild(compSD);
  breakdown.appendChild(compN);
  breakdown.appendChild(compB);
  teamDiv.appendChild(breakdown);

  headerLeft.appendChild(badge);
  headerLeft.appendChild(label);

  const headerRight = document.createElement('div');
  headerRight.style.color = '#fbbf24';
  headerRight.style.fontWeight = '700';
  headerRight.textContent = `${total} PWR`;

  teamHeader.appendChild(headerLeft);
  teamHeader.appendChild(headerRight);
  teamDiv.appendChild(teamHeader);

  const grid = document.createElement('div');
  grid.style.display = 'grid';
  grid.style.gridTemplateColumns = 'repeat(7, auto)';
  grid.style.gap = '12px';
  grid.style.overflowX = 'auto';

  const byEmotion = {};
  team.stickers.forEach(s => {
    byEmotion[s.emotion] = s;
  });
  emotionOrder.forEach(emotion => {
    const sticker = byEmotion[emotion];
    if (sticker) {
      const callbacks = {
        isInBasket: (addr) => appState.basket.has(addr),
        onBasketToggle: (st, btn) => {
          console.log('[portfolio.renderTeam] onBasketToggle called for', st.address);
          if (appState.basket.has(st.address)) {
            // already in basket – remove
            basket.toggleBasket(st.address, st, appState, portfolioState, exchangeState, exchangeMapping, {
              updateBasketBtn: (addr, isIn) => {
                console.log('[portfolio.renderTeam] updateBasketBtn called, isIn?', isIn);
                btn.textContent = isIn ? '✓' : '+';
                btn.classList.toggle('active', isIn);
              },
              updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
              updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
              rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
              updatePortfolioIfActive: () => {
                if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
                  const walletResults = portfolioState.lastStickerResults || [];
                  const currentIdx = portfolioState.currentWalletIndex || 0;
                  portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
                }
              }
            });
          } else {
            // new addition – ask for recipient
            showRecipientMenu(btn, null, {
              stickerData: {
                address: st.address,
                name: st.name,
                image_url: st.image_url,
                skin_tone: (st.skin_tone || st.skin || st.skinTone) || 'Unknown',
                emotion: st.emotion,
                score: st.score,
                wallet_address: st.wallet_address || st.owner,
                owner: st.wallet_address || st.owner
              },
              onSelect: (recipientAddr) => {
                const stickerData = {
                  address: st.address,
                  name: st.name,
                  image_url: st.image_url,
                  skin_tone: (st.skin_tone || st.skin || st.skinTone) || 'Unknown',
                  emotion: st.emotion,
                  score: st.score,
                  wallet_address: st.wallet_address || st.owner,
                  owner: st.wallet_address || st.owner,
                  recipient: recipientAddr
                };
                basket.toggleBasket(st.address, stickerData, appState, portfolioState, exchangeState, exchangeMapping, {
                  updateBasketBtn: (addr, isIn) => {
                    btn.textContent = isIn ? '✓' : '+';
                    btn.classList.toggle('active', isIn);
                  },
                  updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
                  updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
                  rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
                  updatePortfolioIfActive: () => {
                    if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
                      const walletResults = portfolioState.lastStickerResults || [];
                      const currentIdx = portfolioState.currentWalletIndex || 0;
                      portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
                    }
                  }
                });
              }
            });
          }
          console.log('Basket toggle for sticker:', st.address, 'nowIn?', appState.basket.has(st.address));
        }
      };
      const card = renderStickerCardForTeam(sticker, callbacks);
      grid.appendChild(card);
    } else {
      const emptyCard = document.createElement('div');
      emptyCard.className = 'sticker-card empty-card';
      emptyCard.style.display = 'flex';
      emptyCard.style.flexDirection = 'column';
      emptyCard.style.alignItems = 'center';
      emptyCard.style.justifyContent = 'center';
      emptyCard.textContent = '—';
      grid.appendChild(emptyCard);
    }
  });
  teamDiv.appendChild(grid);
  container.appendChild(teamDiv);
}

function renderStickerCardForTeam(sticker, callbacks = {}) {
  return createStickerCard(sticker, callbacks);
}

function switchPortfolioWallet(walletIndex, walletResults, appState, portfolioState, domElements) {
  if (!walletResults || walletIndex < 0 || walletIndex >= walletResults.length) {
    return;
  }
  
  // Update wallet selector UI if present
  const walletButtons = domElements.walletButtons || document.querySelectorAll('.wallet-selector-btn');
  walletButtons.forEach((btn, idx) => {
    btn.classList.toggle('active', idx === walletIndex);
  });
  
  // Render portfolio for this wallet
  renderPortfolio(walletIndex, walletResults, appState, portfolioState, domElements);
}

async function loadAndRenderPortfolios(appState, portfolioState, domElements) {
  try {
    const response = await api.fetchAllWalletsWithTeams();
    const walletResults = response.results || [];

    if (walletResults.length === 0) {
      console.log('No wallets loaded');
      if (domElements.portfolioSection) {
        domElements.portfolioSection.innerHTML = `
          <div class="empty-state">
            <p>👛 No portfolio data available yet.</p>
            <p>Please load some wallets first using the <strong>Load NFTs</strong> button in the sidebar.</p>
          </div>
        `;
      }
      return;
    }
    
    portfolioState.lastStickerResults = walletResults;
    portfolioState.currentWalletIndex = 0;
    
    renderWalletSelector(walletResults, appState, portfolioState, domElements);
    // show summary table at top of portfolio tab
    renderPortfolioStatsTable(walletResults, appState, portfolioState, domElements);
    
    renderPortfolio(0, walletResults, appState, portfolioState, domElements);
    
  } catch (err) {
    console.error('Failed to load portfolios', err);
    if (domElements.portfolioSection) {
      domElements.portfolioSection.innerHTML = `
        <div class="empty-state">
          <p>⚠️ Error loading portfolio data.</p>
          <p>${err.message}</p>
        </div>
      `;
    }
  }
}

function renderWalletSelector(walletResults, appState, portfolioState, domElements) {
  if (!domElements.walletSelector) return;
  
  domElements.walletSelector.innerHTML = '';
  
  // keep a list of addresses for synergy priority dropdown
  appState.availableWallets = walletResults.map(w => w.wallet || w.address || '').filter(a=>a);
  if (domElements && domElements.synergyFilterContainer) {
    // re-render filters to refresh dropdown options if it exists
    renderSynergyFilters(appState, domElements);
  }
  walletResults.forEach((wallet, idx) => {
    const walletAddress = wallet.wallet || wallet.address;
    let pstats = stats.computePortfolioStats(
      wallet.stickers || [],
      null,
      wallet.collection_synergy || null,
      wallet.teams || null
    );
    const btn = document.createElement('button');
    btn.className = 'wallet-selector-btn filter-btn' + (idx === 0 ? ' active' : '');
    btn.textContent = `${helpers.shortAddr(walletAddress)} – ${pstats.stickerCount} стикеров, ${pstats.teamCount} команд, ${pstats.totalPower} PWR ` +
                      `(s:${pstats.stickerPower} sy:${pstats.synergyPower} t:${pstats.teamPower})`;
    btn.title = `${walletAddress}
` + `stickers:${pstats.stickerPower} · synergy:${pstats.synergyPower} · teams:${pstats.teamPower}`;

    const colorClass = getWalletColorClass(walletAddress);
    if (colorClass) btn.classList.add(colorClass);

    btn.addEventListener('click', () => {
      switchPortfolioWallet(idx, walletResults, appState, portfolioState, domElements);
    });

    domElements.walletSelector.appendChild(btn);
  });
  domElements.walletButtons = Array.from(domElements.walletSelector.querySelectorAll('.wallet-selector-btn'));
}

// build a summary table of portfolio stats for all wallets
function renderPortfolioStatsTable(walletResults, appState, portfolioState, domElements) {
  if (!domElements.portfolioStats) return;
  const statsDiv = domElements.portfolioStats;
  statsDiv.innerHTML = '';

  const wallets = walletResults || [];
  if (!wallets.length) {
    statsDiv.innerHTML = '<p class="info-message">No portfolio data available</p>';
    return;
  }

  console.log('DEBUG: renderPortfolioStatsTable wallets:', wallets);
  if (wallets.length > 0) {
    console.log('DEBUG: first wallet stickers:', wallets[0].stickers);
    if (wallets[0].stickers && wallets[0].stickers.length > 0) {
      console.log('DEBUG: first sticker attributes:', wallets[0].stickers[0].attributes);
    }
  }

  // determine whether we have original data (new-portfolio scenario)
  const hasOrig = wallets.some(w => w.orig_stickers || w.orig_teams);
  let html = '<table class="wallet-stats-table table-small" style="background:rgba(255,255,255,0.02);">'
           + '<tr>'
           + '<th>Wallet</th><th># stickers</th><th>teams 7</th>'
           + '<th>stickers PWR</th><th>synergy PWR</th><th>team PWR</th><th>total PWR</th>'
           + (hasOrig ? '<th>∆ # stickers</th><th>∆ teams7</th><th>∆ stickers PWR</th><th>∆ synergy PWR</th><th>∆ team PWR</th><th>∆ total PWR</th>' : '')
           + '</tr>';
  wallets.forEach(w => {
    const addr = w.wallet || w.address || '';
    const statsObj = stats.computePortfolioStats(w.stickers || [], null, w.collection_synergy || null, w.teams || null);
    const sizeCounts = statsObj.teamSizeCounts || {};
    let deltaHtml = '';
    if (hasOrig) {
      // compute original stats if available
      const origStats = stats.computePortfolioStats(w.orig_stickers||[], null, w.collection_synergy || null, w.orig_teams || null);
      const deltaCount = (statsObj.stickerCount||0) - (origStats.stickerCount||0);
      const deltaTeams7 = (statsObj.teamSizeCounts?.[7]||0) - (origStats.teamSizeCounts?.[7]||0);
      const deltaStickerPwr = (statsObj.stickerPower||0) - (origStats.stickerPower||0);
      const deltaSynergyPwr = (statsObj.synergyPower||0) - (origStats.synergyPower||0);
      const deltaTeamPwr = (statsObj.teamPower||0) - (origStats.teamPower||0);
      const deltaTotal = (statsObj.totalPower||0) - (origStats.totalPower||0);
      deltaHtml = `<td>${deltaCount>=0?'+':''}${deltaCount}</td>`
               + `<td>${deltaTeams7>=0?'+':''}${deltaTeams7}</td>`
               + `<td>${deltaStickerPwr>=0?'+':''}${deltaStickerPwr}</td>`
               + `<td>${deltaSynergyPwr>=0?'+':''}${deltaSynergyPwr}</td>`
               + `<td>${deltaTeamPwr>=0?'+':''}${deltaTeamPwr}</td>`
               + `<td>${deltaTotal>=0?'+':''}${deltaTotal}</td>`;
    }
    html += `<tr><td title="${addr}">${helpers.shortAddr(addr)}</td>`
         + `<td>${statsObj.stickerCount || 0}</td>`
         + `<td>${sizeCounts[7]||0}</td>`
         + `<td>${statsObj.stickerPower||0}</td><td>${statsObj.synergyPower||0}</td><td>${statsObj.teamPower||0}</td><td>${statsObj.totalPower||0}</td>`
         + deltaHtml + `</tr>`;
  });
  html += '</table>';
  statsDiv.innerHTML = html;

  // Attribute counts table (sorted with priority attributes first)
  const attrPriority = [
    'Bitcoin', 'ETH', 'TON', 'Telegram', 'Dollar', 'RUB', 'Zargates', 'Tribo Games', 'Elephant'
  ];
  const grouped = {};
  (wallets || []).forEach(w => {
    const walletAddr = w.wallet || w.address || '';
    grouped[walletAddr] = w.stickers || [];
  });
  const attrCounts = computeAttributeCountsByGroup(grouped, attrPriority);
  renderAttributeStatsTable(statsDiv, attrCounts, attrPriority);
}


console.log('modules/portfolio.js loaded');

// attach to global object
portfolio.renderPortfolio = renderPortfolio;
portfolio.switchPortfolioWallet = switchPortfolioWallet;
portfolio.loadAndRenderPortfolios = loadAndRenderPortfolios;

// ===============================
// SECTION: modules/synergy.js
// ===============================
/**
 * modules/synergy.js — Synergy tab logic
 * (originally in modules/synergy.js)
 */

async function loadSkins(appState) {
  if (appState.availableSkins && appState.availableSkins.length) {
    return appState.availableSkins;
  }
  try {
    const response = await api.fetchSkins();
    const skins = response.skins || [];
    appState.availableSkins = skins;
    return skins;
  } catch (err) {
    console.error('Failed to load skins', err);
    return [];
  }
}

async function loadAttributeGroups(appState) {
  try {
    const response = await api.fetchAttributeGroups();
    const groups = response.groups || [];
    appState.availableAttributeGroups = groups;
    return groups;
  } catch (err) {
    console.error('Failed to load attribute groups', err);
    return [];
  }
}

async function renderWalletStats(appState, domElements) {
  if (!domElements.synergyStats) return;
  const statsDiv = domElements.synergyStats;
  statsDiv.innerHTML = '<p>Loading synergy statistics…</p>';

  try {
    const synergies = appState.currentSynergies || {};
    if (!synergies || Object.keys(synergies).length === 0) {
      statsDiv.innerHTML = '<p class="info-message">Нет синергий</p>';
      return;
    }

    // compute total counts by team size across all synergies
    const totals = {7:0,6:0,5:0,4:0,3:0};
    Object.values(synergies).forEach(syn => {
      (syn.rows || []).forEach(row => {
        // attribute count is preferred when available; fall back to sticker count
        let size = row.row_attr_count != null ? row.row_attr_count : 0;
        if (size === 0) {
          (row.wallet_groups || []).forEach(wg => {
            if (wg.stickers && Array.isArray(wg.stickers)) {
              size += wg.stickers.length;
            }
          });
        }
        if (size >= 3 && size <= 7) totals[size] += 1;
      });
    });

    let html = '<table class="wallet-stats-table table-small" style="background:rgba(255,255,255,0.02);">'
             + '<tr><th>7</th><th>6</th><th>5</th><th>4</th><th>3</th></tr>';
    html += `<tr><td>${totals[7]}</td><td>${totals[6]}</td><td>${totals[5]}</td><td>${totals[4]}</td><td>${totals[3]}</td></tr>`;
    html += '</table>';

    statsDiv.innerHTML = html;
  } catch (err) {
    console.error('Error loading wallet stats', err);
    statsDiv.innerHTML = '<p class="error">Unable to load wallet stats</p>';
  }
}

async function loadSynergies(appState) {
  try {
    const params = [];
    if (appState.selectedWalletPriority) {
      params.push(`wallet_priority=${encodeURIComponent(appState.selectedWalletPriority)}`);
    }
    const response = await api.fetchSynergies(params.join('&'));
    appState.currentSynergies = response.synergies || {};
    return appState.currentSynergies;
  } catch (err) {
    console.error('Failed to load synergies', err);
    return {};
  }
}

async function initializeSynergyTab(appState, domElements) {
  try {
    if (domElements.loadingMessage) domElements.loadingMessage.style.display = 'block';
    if (domElements.selectionMessage) domElements.selectionMessage.style.display = 'none';
    if (domElements.synergyResults) domElements.synergyResults.style.display = 'none';
    if (domElements.synergyContent) domElements.synergyContent.style.display = 'block';

    const skins = await loadSkins(appState);
    const groups = await loadAttributeGroups(appState);
    if (skins.length === 0 || groups.length === 0) {
      if (domElements.synergySection) {
        domElements.synergySection.innerHTML = `
          <div class="empty-state">
            <p>📊 No synergy data available yet.</p>
            <p>Please load some wallets first using the <strong>Load NFTs</strong> button in the sidebar.</p>
          </div>
        `;
      }
      if (domElements.synergyContent) domElements.synergyContent.style.display = 'none';
      if (domElements.loadingMessage) domElements.loadingMessage.style.display = 'none';
      return { skins, groups };
    }
    appState.availableSkins = skins;
    appState.availableAttributeGroups = groups;
    renderWalletStats(appState, domElements);
    renderSynergyFilters(appState, domElements);
    if (domElements.loadingMessage) domElements.loadingMessage.style.display = 'none';
    return { skins, groups };
  } catch (err) {
    console.error('Failed to initialize synergy tab', err);
    if (domElements.synergySection) {
      domElements.synergySection.innerHTML = `
        <div class="empty-state">
          <p>⚠️ Error loading synergy data.</p>
          <p>${err.message}</p>
        </div>
      `;
    }
    if (domElements.synergyContent) domElements.synergyContent.style.display = 'none';
  }
}

function insertSynergyToolbar(domElements) {
  if (!domElements.synergyContent) return;
  let toolbar = domElements.synergyContent.querySelector('.synergy-toolbar');
  if (!toolbar) {
    toolbar = document.createElement('div');
    toolbar.className = 'synergy-toolbar';
    toolbar.style.marginBottom = '12px';
    domElements.synergyContent.insertBefore(toolbar, domElements.synergyContent.firstChild);
  } else {
    toolbar.innerHTML = '';
  }
  if (domElements.loadBtn) { const load = domElements.loadBtn.cloneNode(true); load.addEventListener('click', () => domElements.loadBtn.click()); toolbar.appendChild(load); }
  if (domElements.clearBtn) { const clear = domElements.clearBtn.cloneNode(true); clear.addEventListener('click', () => domElements.clearBtn.click()); toolbar.appendChild(clear); }
}

function renderSynergyFilters(appState, domElements) {
  if (!domElements.synergyFilterContainer) return;
  const container = domElements.synergyFilterContainer;
  container.innerHTML = '';

  // priority wallet select
  const priorityDiv = document.createElement('div');
  priorityDiv.style.display = 'inline-flex';
  priorityDiv.style.alignItems = 'center';
  // no bottom margin; spacing controlled by .filters gap
  const priorityLabel = document.createElement('label');
  priorityLabel.textContent = 'Priority:';
  priorityLabel.style.fontSize = '12px';
  priorityLabel.style.marginRight = '4px';
  const prioritySelect = document.createElement('select');
  prioritySelect.id = 'priority-wallet-select';
  prioritySelect.className = 'filter-btn';
  prioritySelect.style.minWidth = '180px';
  prioritySelect.addEventListener('change', () => {
    const val = prioritySelect.value || null;
    appState.selectedWalletPriority = val;
    loadSynergiesForFilters(appState, domElements);
  });
  priorityDiv.appendChild(priorityLabel);
  priorityDiv.appendChild(prioritySelect);
  container.appendChild(priorityDiv);

  const skinsDiv = document.createElement('div');
  skinsDiv.id = 'skins-container';
  skinsDiv.className = 'button-grid';
  const allSkinBtn = document.createElement('button');
  allSkinBtn.className = 'filter-btn';
  allSkinBtn.textContent = 'All';
  allSkinBtn.addEventListener('click', () => {
    skinsDiv.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    allSkinBtn.classList.add('active');
    appState.selectedSkin = 'ALL';
    loadSynergiesForFilters(appState, domElements);
  });
  skinsDiv.appendChild(allSkinBtn);
  const skins = appState.availableSkins || [];
  // refresh priority options whenever filters are rendered
  const walletList = appState.availableWallets || [];
  prioritySelect.innerHTML = '';
  const noneOpt = document.createElement('option');
  noneOpt.value = '';
  noneOpt.textContent = '(none)';
  prioritySelect.appendChild(noneOpt);
  walletList.forEach(addr => {
    const opt = document.createElement('option');
    opt.value = addr;
    opt.textContent = addr.substring(0,6) + '...' + addr.slice(-4);
    prioritySelect.appendChild(opt);
  });
  skins.forEach(skin => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.textContent = skin.substring(0, 8);
    btn.title = skin;
    btn.addEventListener('click', () => {
      skinsDiv.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      appState.selectedSkin = skin;
      loadSynergiesForFilters(appState, domElements);
    });
    skinsDiv.appendChild(btn);
  });

  container.appendChild(skinsDiv);

  // Group buttons
  const groupsDiv = document.createElement('div');
  groupsDiv.id = 'groups-container';
  groupsDiv.className = 'button-grid';

  const allGroupBtn = document.createElement('button');
  allGroupBtn.className = 'filter-btn';
  allGroupBtn.textContent = 'All';
  allGroupBtn.addEventListener('click', () => {
    groupsDiv.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    allGroupBtn.classList.add('active');
    appState.selectedGroup = 'ALL';
    loadSynergiesForFilters(appState, domElements);
  });
  groupsDiv.appendChild(allGroupBtn);

  const groups = appState.availableAttributeGroups || [];
  groups.forEach(group => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.textContent = group;
    btn.addEventListener('click', () => {
      groupsDiv.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      appState.selectedGroup = group;
      loadSynergiesForFilters(appState, domElements);
    });
    groupsDiv.appendChild(btn);
  });

  container.appendChild(groupsDiv);

  // default to All/All and load all synergies immediately
  allSkinBtn.classList.add('active');
  allGroupBtn.classList.add('active');
  appState.selectedSkin = 'ALL';
  appState.selectedGroup = 'ALL';
  appState.selectedWalletPriority = null;
  loadSynergiesForFilters(appState, domElements);
}

// loadSynergiesForFilters and supporting functions
async function loadSynergiesForFilters(appState, domElements) {
  const hasSkin = appState.selectedSkin !== null && appState.selectedSkin !== undefined;
  const hasGroup = appState.selectedGroup !== null && appState.selectedGroup !== undefined;
  
  if (!hasSkin || !hasGroup) {
    if (domElements.selectionMessage) domElements.selectionMessage.style.display = 'block';
    if (domElements.synergyResults) domElements.synergyResults.style.display = 'none';
    return;
  }
  
  if (domElements.selectionMessage) domElements.selectionMessage.style.display = 'none';
  if (domElements.synergyResults) domElements.synergyResults.style.display = 'block';
  
  try {
    const baseGroupParam = (appState.selectedGroup && appState.selectedGroup !== 'ALL')
      ? `attribute_group=${encodeURIComponent(appState.selectedGroup)}`
      : '';
    const priorityParam = appState.selectedWalletPriority
      ? `wallet_priority=${encodeURIComponent(appState.selectedWalletPriority)}`
      : '';
    // if user selected ALL skins and we have a list, fetch each separately
    if (appState.selectedSkin === 'ALL' && appState.availableSkins && appState.availableSkins.length) {
      console.log('Fetching synergies for ALL skins separately');
      const merged = {};
      for (const skin of appState.availableSkins) {
        const parts = [];
        if (skin) parts.push(`skin_tone=${encodeURIComponent(skin)}`);
        if (baseGroupParam) parts.push(baseGroupParam);
        if (priorityParam) parts.push(priorityParam);
        const skinQuery = parts.join('&');
        console.log('  skin query', skinQuery);
        // try cache first
        let resp;
        if (_synergiesCache[skinQuery]) {
          resp = { synergies: _synergiesCache[skinQuery] };
        } else {
          resp = await api.fetchSynergies(skinQuery);
          _synergiesCache[skinQuery] = resp.synergies || {};
        }
        const sy = resp.synergies || {};
        Object.entries(sy).forEach(([key, data]) => {
          const newKey = `${skin} :: ${key}`;
          data.skin_tone = skin;
          merged[newKey] = data;
        });
      }
      response = { synergies: merged };
    } else {
      const params = [];
      if (appState.selectedSkin && appState.selectedSkin !== 'ALL') {
        params.push(`skin_tone=${encodeURIComponent(appState.selectedSkin)}`);
      }
      if (baseGroupParam) {
        params.push(baseGroupParam);
      }
      if (priorityParam) {
        params.push(priorityParam);
      }
      const query = params.length ? params.join('&') : '';
      console.log('Fetching synergies with query:', query);
      if (_synergiesCache[query]) {
        response = { synergies: _synergiesCache[query] };
      } else {
        response = await api.fetchSynergies(query);
        _synergiesCache[query] = response.synergies || {};
      }
    }
    
    if (!response || !response.synergies || typeof response.synergies !== 'object') {
      console.error('Synergies API returned invalid data', response);
      if (domElements.synergySection) {
        domElements.synergySection.innerHTML = '<p class="no-synergies">No synergies found for selected filters</p>';
      }
      return;
    }
    
    appState.currentSynergies = response.synergies;
    console.log('Synergies fetched, count=', Object.keys(appState.currentSynergies).length, 'data=', appState.currentSynergies);

    if ((appState.selectedSkin && appState.selectedSkin !== 'ALL') ||
        (appState.selectedGroup && appState.selectedGroup !== 'ALL')) {
      const sample = Object.values(appState.currentSynergies).slice(0,3);
      sample.forEach(d => {
        if (d.skin_tone === 'ALL' || d.attribute_group === 'ALL') {
          console.warn('Server returned wildcard metadata with filters active', d);
        }
      });
    }

    renderAllSynergiesGlobal(appState, domElements);
    // refresh wallet statistics so that synergy size counts appear
    renderWalletStats(appState, domElements);
  } catch (err) {
    console.error('Error loading synergies', err);
    if (domElements.synergySection) {
      domElements.synergySection.innerHTML = `<p class="no-synergies">Error: ${err.message}</p>`;
    }
  }
}

function renderAllSynergiesGlobal(appState, domElements) {
  if (!domElements.synergySection) return;

  const container = domElements.synergySection;
  container.innerHTML = '';

  const synergies = appState.currentSynergies || {};
  const selectedSkin = appState.selectedSkin || '';
  const selectedGroup = appState.selectedGroup || '';

  if (!synergies || typeof synergies !== 'object' || Object.keys(synergies).length === 0) {
    container.innerHTML = '<p class="no-synergies">No synergies found</p>';
    return;
  }

  const grouped = {};
  Object.entries(synergies).forEach(([key, data]) => {
    const ds = data.skin_tone || 'ALL';
    const dg = data.attribute_group || 'ALL';
    if (selectedSkin && selectedSkin !== 'ALL' && ds !== 'ALL' && ds !== selectedSkin) return;
    if (selectedGroup && selectedGroup !== 'ALL' && dg !== 'ALL' && dg !== selectedGroup) return;
    const attrValue = data.attribute_value || key;
    const skin = ds;
    const count = data.total_count || 0;
    let groupKey = attrValue;
    if (
      selectedSkin === 'ALL' &&
      skin !== 'ALL' &&
      !attrValue.includes(' :: ')
    ) {
      groupKey = `${skin} :: ${attrValue}`;
    }
    if (!grouped[groupKey]) grouped[groupKey] = [];
    grouped[groupKey].push({ skin, data, count });
  });

  if (Object.keys(grouped).length === 0) {
    console.debug('renderAllSynergiesGlobal – no groups after filtering', {
      selectedSkin,
      selectedGroup,
      synergiesSample: Object.entries(synergies).slice(0,5)
    });
    container.innerHTML = '<p class="no-synergies">No synergies found for selected filters</p>';
    return;
  }

  let groupEntries = Object.entries(grouped);
  if (appState.selectedSkin === 'ALL') {
    const globalMax = {};
    groupEntries.forEach(([key, arr]) => {
      const attr = key.includes(' :: ') ? key.split(' :: ')[1] : key;
      const maxRow = Math.max(...arr.map(i => i.data?.max_row_count || 0));
      globalMax[attr] = Math.max(globalMax[attr] || 0, maxRow);
    });
    groupEntries.sort((a,b) => {
      const attrA = a[0].includes(' :: ') ? a[0].split(' :: ')[1] : a[0];
      const attrB = b[0].includes(' :: ') ? b[0].split(' :: ')[1] : b[0];
      const diff = (globalMax[attrB] || 0) - (globalMax[attrA] || 0);
      if (diff !== 0) return diff;
      const maxA = Math.max(...a[1].map(item => item.data?.max_row_count || 0));
      const maxB = Math.max(...b[1].map(item => item.data?.max_row_count || 0));
      if (maxB !== maxA) return maxB - maxA;
      const totalA = a[1].reduce((s,i)=>s+(i.count||0),0);
      const totalB = b[1].reduce((s,i)=>s+(i.count||0),0);
      return totalB - totalA;
    });
  }
  groupEntries.forEach(([groupKey, arr]) => {
    let displayAttr = groupKey;
    if (groupKey.includes(' :: ')) {
      const [skinPart, attrPart] = groupKey.split(' :: ');
      displayAttr = attrPart;
      arr.forEach(item => { item.skin = skinPart; });
    }
    renderSynergiesGlobal(container, displayAttr, arr, appState, domElements);
  });
}

function renderSynergiesGlobal(container, attrValue, bySkinsArray, appState, domElements) {
  const totalCount = bySkinsArray.reduce((sum, item) => sum + (item.count || 0), 0);
  const section = document.createElement('div');
  section.className = 'synergy-section';
  // collapsible content wrapper
  const contentWrapper = document.createElement('div');
  contentWrapper.className = 'synergy-content-wrapper';
  let titleText = attrValue;
  const skinsSet = new Set(bySkinsArray.map(i => i.skin));
  if (skinsSet.size === 1) {
    const onlySkin = Array.from(skinsSet)[0];
    if (onlySkin && onlySkin !== 'ALL') {
      titleText = `${onlySkin} – ${attrValue}`;
    }
  }
  const header = document.createElement('div');
  header.className = 'synergy-header';
  header.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="synergy-icon">⚔️</span>
      <span class="synergy-count">${titleText}</span>
    </div>
    <div style="color:#9be7ff;">(${totalCount} items total)</div>
  `;
  // collapse/expand button
  const toggleBtn = document.createElement('button');
  toggleBtn.className = 'collapse-btn';
  toggleBtn.textContent = '\u25BC';
  // use auto margin to push button to the far right edge of header
  toggleBtn.style.marginLeft = 'auto';
  toggleBtn.addEventListener('click', () => {
    const collapsed = contentWrapper.classList.toggle('collapsed');
    toggleBtn.textContent = collapsed ? '\u25B6' : '\u25BC';
    contentWrapper.style.display = collapsed ? 'none' : '';
  });
  header.appendChild(toggleBtn);
  section.appendChild(header);
  // add wrapper element so rows and labels go inside it
  section.appendChild(contentWrapper);
  const allRows = [];
  let seq = 0;
  bySkinsArray.forEach(({ skin, data }) => {
    const rows = data.rows || [];
    rows.forEach(rowEntry => {
      let walletGroups, emotions;
      if (Array.isArray(rowEntry)) {
        walletGroups = rowEntry;
        emotions = [];
      } else {
        walletGroups = rowEntry.wallet_groups || [];
        emotions = rowEntry.emotions || [];
      }
      const stickerCount = walletGroups.reduce(
        (sum, grp) => sum + (grp.stickers ? grp.stickers.length : 0),
        0
      );
      const attrCount = rowEntry.row_attr_count != null ? rowEntry.row_attr_count : stickerCount;
      allRows.push({ skin, walletGroups, stickerCount, attrCount, emotions, data, originalIndex: seq++ });
    });
  });
  // if there are no wallet groups at all, the synergy has no stickers
  if (allRows.length === 0) {
    console.warn('renderSynergiesGlobal: no rows found for', attrValue, 'skins', bySkinsArray);
    const note = document.createElement('div');
    note.className = 'empty-state';
    note.textContent = '(no stickers available for this synergy)';
    // wrapper is already appended above; just put note inside
    contentWrapper.appendChild(note);
    container.appendChild(section);
    return;
  }
  allRows.forEach(r => {
    r.rowPower = r.walletGroups.reduce((sum, wg) => {
      return sum + wg.stickers.reduce((s, st) => s + (st.score || 0), 0);
    }, 0);
  });
  allRows.sort((a, b) => {
    // sort primarily by attribute count when available, otherwise fall back to sticker count
    const countA = a.attrCount != null ? a.attrCount : a.stickerCount;
    const countB = b.attrCount != null ? b.attrCount : b.stickerCount;
    if (countB !== countA) return countB - countA;
    if ((b.rowPower || 0) !== (a.rowPower || 0)) return (b.rowPower || 0) - (a.rowPower || 0);
    return (a.originalIndex || 0) - (b.originalIndex || 0);
  });
  allRows.forEach(({ skin, walletGroups, stickerCount, attrCount, emotions, data }, rowIndex) => {
    const skinHeader = document.createElement('div');
    if (emotions && emotions.length) {
      const emotionLabel = document.createElement('div');
      emotionLabel.style.fontSize = '11px';
      emotionLabel.style.color = '#f1f1f1';
      emotionLabel.textContent = `emotions: ${emotions.join(', ')}`;
      contentWrapper.appendChild(emotionLabel);
    }
    skinHeader.style.color = '#9be7ff';
    skinHeader.style.fontSize = '13px';
    skinHeader.style.fontWeight = '600';
    skinHeader.style.marginTop = '10px';
    skinHeader.style.marginBottom = '6px';
    // Use data.max_row_count (attribute count) from API, not recalculated sticker count
    const displayCount = data?.max_row_count || attrCount || stickerCount;
    skinHeader.textContent = `🎨 ${skin} (${displayCount} атрибутов, ${stickerCount} стикеров)`;
    contentWrapper.appendChild(skinHeader);
    const scrollRow = document.createElement('div');
    scrollRow.className = 'stickers-scroll-row';
    walletGroups.forEach(group => {
      const walletContainer = document.createElement('div');
      walletContainer.className = 'wallet-group ' + getWalletColorClass(group.wallet_address);
      walletContainer.style.display = 'flex';
      walletContainer.style.flexDirection = 'column';
      walletContainer.style.alignItems = 'center';
      walletContainer.style.padding = '6px';
      walletContainer.style.borderRadius = '10px';
      walletContainer.style.marginRight = '18px';
      const walletHeader = document.createElement('div');
      walletHeader.className = 'wallet-header-bar';
      walletHeader.textContent = group.wallet_address ?
        `${group.wallet_address.substring(0,6)}...${group.wallet_address.slice(-4)}` : 'Unknown';
      walletContainer.appendChild(walletHeader);
      const cardsInner = document.createElement('div');
      cardsInner.className = 'wallet-cards-inner';
      cardsInner.style.display = 'flex';
      if (!Array.isArray(group.stickers)) {
        console.warn('expected wallet group stickers array but got', group.stickers, 'for group', attrValue, 'skin', skin);
      } else if (group.stickers.length === 0) {
        console.warn('wallet group has zero stickers', group, 'for group', attrValue, 'skin', skin);
      }
      group.stickers.forEach(sticker => {
        // sticker may be a plain string (address) or full object
        let stObj = sticker;
        if (typeof sticker === 'string' || !sticker || !sticker.address) {
          console.warn('synergy row contains non-object sticker', sticker);
          stObj = {
            address: sticker || '',
            name: sticker || '',
            image_url: '',
            skin_tone: '',
            emotion: '',
            score: 0,
            attr_value: 0,
            synergy_bonus: 0,
            name_value: 0,
            synergies: sticker.synergies || []
          };
        } else if (!stObj.synergies) {
          // ensure synergies field exists even if it's an empty array
          stObj.synergies = stObj.synergies || [];
        }
        
        const callbacks = {
          isInBasket: (addr) => appState.basket.has(addr),
          onBasketToggle: (st, btn) => {
            // NOTE: st here is the stObject passed from createStickerCard, which has synergies
            if (appState.basket.has(st.address)) {
              // already in basket — remove directly
              basket.toggleBasket(st.address, st, appState, portfolioState, exchangeState, exchangeMapping, {
                updateBasketBtn: (addr, isIn) => {
                  btn.textContent = isIn ? '✓' : '+';
                  btn.classList.toggle('active', isIn);
                },
                updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
                updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
                rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
                updatePortfolioIfActive: () => {
                  if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
                    const walletResults = portfolioState.lastStickerResults || [];
                    const currentIdx = portfolioState.currentWalletIndex || 0;
                    portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
                  }
                }
              });
            } else {
              // not in basket yet – select recipient
              showRecipientMenu(btn, null, {
                stickerData: {
                  address: st.address,
                  name: st.name,
                  image_url: st.image_url,
                  skin_tone: (st.skin_tone || st.skin || st.skinTone) || 'Unknown',
                  emotion: st.emotion,
                  score: st.score,
                  wallet_address: st.wallet_address || st.owner,
                  owner: st.wallet_address || st.owner
                },
                onSelect: (recipientAddr) => {
                  const stickerData = {
                    address: st.address,
                    name: st.name,
                    image_url: st.image_url,
                    skin_tone: (st.skin_tone || st.skin || st.skinTone) || 'Unknown',
                    emotion: st.emotion,
                    score: st.score,
                    wallet_address: st.wallet_address || st.owner,
                    owner: st.wallet_address || st.owner,
                    recipient: recipientAddr
                  };
                  basket.toggleBasket(st.address, stickerData, appState, portfolioState, exchangeState, exchangeMapping, {
                    updateBasketBtn: (addr, isIn) => {
                      btn.textContent = isIn ? '✓' : '+';
                      btn.classList.toggle('active', isIn);
                    },
                    updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
                    updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
                    rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
                    updatePortfolioIfActive: () => {
                      if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
                        const walletResults = portfolioState.lastStickerResults || [];
                        const currentIdx = portfolioState.currentWalletIndex || 0;
                        portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
                      }
                    }
                  });
                }
              });
            }
          }
        };
        const card = createStickerCard(stObj, callbacks);
        card.style.marginRight = '0px';
        cardsInner.appendChild(card);
      });
      walletContainer.appendChild(cardsInner);
      scrollRow.appendChild(walletContainer);
    });
    contentWrapper.appendChild(scrollRow);
  });
  container.appendChild(section);
}

console.log('modules/synergy.js loaded');

// expose functions to global object
synergy.loadSkins = loadSkins;
synergy.loadAttributeGroups = loadAttributeGroups;
synergy.loadSynergies = loadSynergies;
synergy.initializeSynergyTab = initializeSynergyTab;
synergy.loadSynergiesForFilters = loadSynergiesForFilters;
synergy.renderAllSynergiesGlobal = renderAllSynergiesGlobal;

// small utility: render dropdown menu near button to pick recipient
function showRecipientMenu(button, stickerAddress, opts = {}) {
  // opts: { stickerData, onSelect }
  console.log('showRecipientMenu wallets count', (appState.walletsInDb||[]).length, 'raw', appState.walletsInDb);
  // remove existing menu if any
  const existing = document.querySelector('.recipient-menu');
  if (existing) existing.remove();

  // create real select element to make native dropdown
  const select = document.createElement('select');
  select.className = 'recipient-menu';
  select.style.position = 'absolute';
  select.style.background = '#1a2332';
  select.style.border = '1px solid #444';
  select.style.borderRadius = '4px';
  select.style.padding = '2px';
  select.style.zIndex = 1000;
  select.style.color = '#fff';
  select.style.minWidth = '140px';
  select.style.maxWidth = '200px';
  select.style.fontSize = '13px';

  const shouldDisable = (addr) => {
    if (stickerAddress) {
      const st = appState.basket.get(stickerAddress);
      if (st) {
        if (st.owner === addr) return true;
        if (st.recipient && st.recipient === addr) return true;
      }
    } else if (opts.stickerData) {
      if (opts.stickerData.owner === addr) return true;
    }
    return false;
  };

  // compute eligible addresses first
  const allAddrs = (appState.walletsInDb || []).map(w => typeof w === 'string' ? w : (w.address || w));
  const disabledAddrs = allAddrs.filter(addr => shouldDisable(addr));
  const choices = allAddrs.filter(addr => addr && !shouldDisable(addr));
  console.log(' showRecipientMenu filter: all', allAddrs, 'disabled', disabledAddrs, 'choices', choices);

  const placeholder = document.createElement('option');
  placeholder.textContent = '-- выберите кошелёк --';
  placeholder.disabled = true;
  placeholder.selected = true;
  select.appendChild(placeholder);

  if (choices.length === 0) {
    const emptyOption = document.createElement('option');
    emptyOption.textContent = '(нет доступных)';
    emptyOption.disabled = true;
    select.appendChild(emptyOption);
  } else {
    choices.forEach(addr => {
      const opt = document.createElement('option');
      opt.value = addr;
      opt.textContent = helpers.shortAddr(addr);
      select.appendChild(opt);
    });
  }

  select.addEventListener('change', () => {
    const chosen = select.value;
    if (opts.onSelect) {
      opts.onSelect(chosen);
    } else if (stickerAddress) {
      const st = appState.basket.get(stickerAddress);
      if (st) {
        const newData = Object.assign({}, st, { recipient: chosen });
        basket.updateBasketSticker(newData, appState, {
          updateBasketBtn: () => {},
          onBasketUpdated: () => {
            updateOriginalBaskets(appState, domElements);
            updateExchangeBaskets(appState, portfolioState, exchangeState, domElements);
          }
        });
      }
    }
    select.remove();
  });

  document.addEventListener('click', function onDocClick(ev) {
    if (!select.contains(ev.target) && ev.target !== button) {
      select.remove();
      document.removeEventListener('click', onDocClick);
    }
  });

  const rect = button.getBoundingClientRect();
  select.style.top = (rect.bottom + window.scrollY) + 'px';
  select.style.left = (rect.left + window.scrollX) + 'px';
  document.body.appendChild(select);
  select.focus();
}

// reattach domElements callbacks lost during earlier patch
  domElements.removeFromBasketCallback = (addr) => {
  basket.removeFromBasket(addr, appState, portfolioState, exchangeState, exchangeMapping, {
    onBasketUpdated: () => {
      updateExchangeBaskets(appState, portfolioState, exchangeState, domElements);
      if (domElements.updateOriginalBaskets) domElements.updateOriginalBaskets(appState, domElements);
    },
    updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
    updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
    rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
    updatePortfolioIfActive: () => {
      if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
        const walletResults = portfolioState.lastStickerResults || [];
        const currentIdx = portfolioState.currentWalletIndex || 0;
        portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
      }
    }
  });
};

// allow other modules to display recipient dropdown
  domElements.showRecipientMenuCallback = (btn, addr) => showRecipientMenu(btn, addr);

domElements.toggleBasketCallback = async (addr, data) => {
  // attempt to locate a button element for positioning the recipient menu
  const btn = document.querySelector(`[data-sticker-address="${addr}"]`);
  if (appState.basket.has(addr)) {
    // already in basket – just remove and update button
    await basket.toggleBasket(addr, data, appState, portfolioState, exchangeState, exchangeMapping, {
      updateBasketBtn: (a, isIn) => {
        if (btn) {
          btn.textContent = isIn ? '✓' : '+';
          btn.classList.toggle('active', isIn);
        }
      },
      updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
      updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
      rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
      updatePortfolioIfActive: () => {
        if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
          const walletResults = portfolioState.lastStickerResults || [];
          const currentIdx = portfolioState.currentWalletIndex || 0;
          portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
        }
      }
    });
  } else {
    // new addition – ask for recipient first
    showRecipientMenu(btn, null, {
      stickerData: {
        address: addr,
        name: data && data.name,
        image_url: data && data.image_url,
        skin_tone: (data && (data.skin_tone || data.skin || data.skinTone)) || 'Unknown',
        emotion: data && data.emotion,
        score: data && data.score,
        wallet_address: (data && (data.wallet_address || data.owner)) || undefined,
        owner: (data && (data.wallet_address || data.owner)) || undefined
      },
      onSelect: (recipientAddr) => {
        const stickerData = {
          address: addr,
          name: data && data.name,
          image_url: data && data.image_url,
          skin_tone: (data && (data.skin_tone || data.skin || data.skinTone)) || 'Unknown',
          emotion: data && data.emotion,
          score: data && data.score,
          wallet_address: (data && (data.wallet_address || data.owner)) || undefined,
          owner: (data && (data.wallet_address || data.owner)) || undefined,
          recipient: recipientAddr
        };
        basket.toggleBasket(addr, stickerData, appState, portfolioState, exchangeState, exchangeMapping, {
          updateBasketBtn: (a, isIn) => {
            if (btn) {
              btn.textContent = isIn ? '✓' : '+';
              btn.classList.toggle('active', isIn);
            }
          },
          updateExchangeBaskets: () => updateExchangeBaskets(appState, domElements),
          updateOriginalBaskets: () => updateOriginalBaskets(appState, domElements),
          rebuildExchange: () => basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping),
          updatePortfolioIfActive: () => {
            if (domElements.portfolioTab && domElements.portfolioTab.classList.contains('active')) {
              const walletResults = portfolioState.lastStickerResults || [];
              const currentIdx = portfolioState.currentWalletIndex || 0;
              portfolio.renderPortfolio(currentIdx, walletResults, appState, portfolioState, domElements);
            }
          }
        });
      }
    });
  }
};

domElements.switchPortfolioWalletCallback = (idx, results) => {
  portfolio.switchPortfolioWallet(idx, results || portfolioState.lastStickerResults, appState, portfolioState, domElements);
};

domElements.loadPortfoliosCallback = async () => {
  await portfolio.loadAndRenderPortfolios(appState, portfolioState, domElements);
};

domElements.initSynergyCallback = async () => {
  await synergy.initializeSynergyTab(appState, domElements);
};

// Initialize on DOMContentLoaded
// ...existing code...

document.addEventListener('DOMContentLoaded', async () => {
  console.log('=== DOMContentLoaded Event ===');

  // restore basket before wiring up event listeners to prevent a visible "refresh" blink
  const basketItems = loadBasketFromStorage();
  console.log('Loaded', basketItems.length, 'basket items from storage');
  appState.basket.clear();
  basketItems.forEach(item => {
    if (item && item.address) {
      appState.basket.set(item.address, item);
    }
  });
  if (domElements.onBasketUpdated) domElements.onBasketUpdated();

  // attempt to override with server data (async)
  await loadBasketFromServer(appState, domElements);

  // fetch wallet list up‑front so recipient menus are populated
  try {
    const walletsResp = await api.fetchWallets();
    appState.walletsInDb = walletsResp.wallets || [];
    console.log('Initialization: fetched', appState.walletsInDb.length, 'wallets');
    if (domElements.walletsInput) {
      domElements.walletsInput.value = appState.walletsInDb.map(w=>w.address).join('\n');
    }
  } catch (e) {
    console.warn('Failed to prefetch wallets', e);
    appState.walletsInDb = [];
  }

  // restore previously active main tab (if any) *before* listeners so no extra save call
  var storedTab = loadActiveTab();
  if (storedTab) {
    console.log('Restoring active tab from storage:', storedTab);
    ui.switchTab(storedTab, appState, exchangeState, portfolioState, domElements);
  }

  // now attach event listeners (this will not reload basket or change tab again)
  ui.setupEventListeners(appState, exchangeState, portfolioState, domElements);

  // rebuild exchange & render the rest of the UI
  basket.rebuildExchangeStateFromBasket(appState, portfolioState, exchangeState, exchangeMapping);
  console.log('Loading portfolio data...');
  await portfolio.loadAndRenderPortfolios(appState, portfolioState, domElements);
  console.log('Loading synergy data...');
  await synergy.initializeSynergyTab(appState, domElements);
  try {
    await synergy.loadSynergiesForFilters(appState, domElements);
  } catch (e) {
    console.warn('re-invoking loadSynergiesForFilters after init failed', e);
  }
  console.log('✓ Application initialized with modular architecture');
  console.log('✓ Basket state:', appState.basket.size, 'items');
  console.log('✓ Portfolio loaded:', portfolioState.lastStickerResults?.length || 0, 'wallets');
  console.log('✓ Ready to accept user input');
});

console.log('main.js execution complete');