(function () {
  if (window.__knowviaWidgetLoaded) return;
  window.__knowviaWidgetLoaded = true;

  var script = document.currentScript;
  if (!script) return;

  var key = script.getAttribute('data-key');
  if (!key) {
    console.error('Knowvia widget: missing data-key attribute.');
    return;
  }

  var origin = new URL(script.src).origin;
  var chatUrl = origin + '/chat?embed=1&key=' + encodeURIComponent(key);

  var ICON_CHAT =
    '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
  var ICON_CLOSE =
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';

  var panel = document.createElement('div');
  panel.style.cssText =
    'position:fixed;right:20px;bottom:88px;width:min(380px,calc(100vw - 40px));' +
    'height:min(600px,calc(100vh - 120px));border-radius:16px;overflow:hidden;' +
    'box-shadow:0 12px 40px rgba(15,23,42,0.28);background:#fff;display:none;' +
    'z-index:2147483000;';

  var frame = null;

  var button = document.createElement('button');
  button.type = 'button';
  button.setAttribute('aria-label', 'Open chat');
  button.style.cssText =
    'position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;' +
    'border:0;background:#0f172a;cursor:pointer;display:flex;align-items:center;' +
    'justify-content:center;box-shadow:0 6px 20px rgba(15,23,42,0.35);' +
    'z-index:2147483001;padding:0;';
  button.innerHTML = ICON_CHAT;

  var open = false;

  function setOpen(next) {
    open = next;
    if (open && !frame) {
      frame = document.createElement('iframe');
      frame.src = chatUrl;
      frame.title = 'Chat assistant';
      frame.style.cssText = 'width:100%;height:100%;border:0;display:block;';
      panel.appendChild(frame);
    }
    panel.style.display = open ? 'block' : 'none';
    button.innerHTML = open ? ICON_CLOSE : ICON_CHAT;
    button.setAttribute('aria-label', open ? 'Close chat' : 'Open chat');
  }

  button.addEventListener('click', function () {
    setOpen(!open);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && open) setOpen(false);
  });

  function mount() {
    document.body.appendChild(panel);
    document.body.appendChild(button);
  }

  if (document.body) mount();
  else document.addEventListener('DOMContentLoaded', mount);
})();
