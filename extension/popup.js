// extension/popup.js
async function init() {
  const { styleData, enabled } = await chrome.storage.local.get(['styleData', 'enabled']);

  const updatedEl = document.getElementById('updated');
  updatedEl.textContent = styleData
    ? `Data updated: ${styleData.updated_at}`
    : 'No data loaded yet';

  const toggle = document.getElementById('enabled');
  toggle.checked = enabled !== false; // default true
  toggle.addEventListener('change', () => {
    chrome.storage.local.set({ enabled: toggle.checked });
  });
}

init();
