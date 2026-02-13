// Seithar Cognitive Threat Scanner — Service Worker

chrome.action.onClicked.addListener(async (tab) => {
  // Popup handles everything; this is a fallback
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'scan') {
    chrome.scripting.executeScript({
      target: { tabId: msg.tabId },
      files: ['content.js']
    }).then(() => {
      chrome.scripting.insertCSS({
        target: { tabId: msg.tabId },
        files: ['styles.css']
      });
    }).then(() => sendResponse({ ok: true }))
      .catch(e => sendResponse({ ok: false, error: e.message }));
    return true;
  }
});
