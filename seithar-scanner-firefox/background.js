// Seithar Cognitive Threat Scanner — Firefox Background Script

browser.browserAction.onClicked.addListener(async (tab) => {
  // Handled by popup
});

browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'scan') {
    browser.tabs.insertCSS(sender.tab.id, { file: 'styles.css' });
    browser.tabs.executeScript(sender.tab.id, { file: 'content.js' });
  }
});
