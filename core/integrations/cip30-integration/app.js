const connectWalletBtn = document.getElementById('connect-wallet');
const getUsedAddressesBtn = document.getElementById('get-used-addresses');
const getUnusedAddressesBtn = document.getElementById('get-unused-addresses');
const getChangeAddressBtn = document.getElementById('get-change-address');
const getRewardAddressesBtn = document.getElementById('get-reward-addresses');

const walletNameEl = document.getElementById('wallet-name');
const walletIconEl = document.getElementById('wallet-icon');
const apiVersionEl = document.getElementById('api-version');
const networkIdEl = document.getElementById('network-id');
const balanceEl = document.getElementById('balance');
const outputPre = document.getElementById('output-pre');

let cardanoApi = null;

function printOutput(data) {
  outputPre.textContent = JSON.stringify(data, null, 2);
}

async function connectWallet() {
  if (window.cardano && window.cardano.nami) {
    try {
      cardanoApi = await window.cardano.nami.enable();
      walletNameEl.textContent = window.cardano.nami.name;
      walletIconEl.src = window.cardano.nami.icon;
      apiVersionEl.textContent = window.cardano.nami.apiVersion;

      const networkId = await cardanoApi.getNetworkId();
      networkIdEl.textContent = networkId === 1 ? 'Mainnet' : 'Testnet';

      const balance = await cardanoApi.getBalance();
      balanceEl.textContent = balance; // This will be CBOR encoded

      printOutput({ message: 'Wallet connected successfully.' });

    } catch (err) {
      console.error(err);
      printOutput({ error: 'Failed to connect wallet.' });
    }
  } else {
    printOutput({ error: 'Cardano wallet not found. Please install Nami or a compatible wallet.' });
  }
}

async function getUsedAddresses() {
  if (!cardanoApi) {
    printOutput({ error: 'Please connect your wallet first.' });
    return;
  }
  try {
    const usedAddresses = await cardanoApi.getUsedAddresses();
    printOutput(usedAddresses);
  } catch (err) {
    console.error(err);
    printOutput({ error: 'Failed to get used addresses.' });
  }
}

async function getUnusedAddresses() {
  if (!cardanoApi) {
    printOutput({ error: 'Please connect your wallet first.' });
    return;
  }
  try {
    const unusedAddresses = await cardanoApi.getUnusedAddresses();
    printOutput(unusedAddresses);
  } catch (err) {
    console.error(err);
    printOutput({ error: 'Failed to get unused addresses.' });
  }
}

async function getChangeAddress() {
  if (!cardanoApi) {
    printOutput({ error: 'Please connect your wallet first.' });
    return;
  }
  try {
    const changeAddress = await cardanoApi.getChangeAddress();
    printOutput(changeAddress);
  } catch (err) {
    console.error(err);
    printOutput({ error: 'Failed to get change address.' });
  }
}

async function getRewardAddresses() {
  if (!cardanoApi) {
    printOutput({ error: 'Please connect your wallet first.' });
    return;
  }
  try {
    const rewardAddresses = await cardanoApi.getRewardAddresses();
    printOutput(rewardAddresses);
  } catch (err) {
    console.error(err);
    printOutput({ error: 'Failed to get reward addresses.' });
  }
}


connectWalletBtn.addEventListener('click', connectWallet);
getUsedAddressesBtn.addEventListener('click', getUsedAddresses);
getUnusedAddressesBtn.addEventListener('click', getUnusedAddresses);
getChangeAddressBtn.addEventListener('click', getChangeAddress);
getRewardAddressesBtn.addEventListener('click', getRewardAddresses);
