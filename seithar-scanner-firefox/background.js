// Seithar Cognitive Threat Scanner — Firefox Background Script

browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'scan') {
    browser.tabs.executeScript(msg.tabId, { file: 'content.js' }).then(() => {
      return browser.tabs.insertCSS(msg.tabId, { file: 'styles.css' });
    }).then(() => sendResponse({ ok: true }))
      .catch(e => sendResponse({ ok: false, error: e.message }));
    return true;
  }
});
