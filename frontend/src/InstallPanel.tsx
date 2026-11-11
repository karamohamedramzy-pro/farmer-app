import React, {useEffect, useState} from 'react';
import {Download, Monitor, Smartphone} from 'lucide-react';
import type {Dict} from './i18n';
import {deviceInfo, hasInstallPrompt, isStandalone, showInstallPrompt, subscribeInstall} from './pwa';

type Message = 'installMobileOther' | 'installDesktopOther' | 'installIos' | 'installAndroid' | 'installComputer' | 'installInFrame' | 'installInsecure' | 'installDone' | 'installDismissed';

/** Both controls install on the current device, or explain how to install on the other device. */
export function InstallPanel({t}: {t: Dict}) {
  const [, update] = useState(0);
  const [message, setMessage] = useState<Message | null>(null);
  useEffect(() => subscribeInstall(() => update(value => value + 1)), []);
  const install = async (target: 'mobile' | 'desktop') => {
    const {mobile, ios} = deviceInfo();
    if (isStandalone()) { setMessage('installDone'); return; }
    if (target === 'mobile' && !mobile) { setMessage('installMobileOther'); return; }
    if (target === 'desktop' && mobile) { setMessage('installDesktopOther'); return; }
    if (!window.isSecureContext) { setMessage('installInsecure'); return; }
    if (window.self !== window.top) { setMessage('installInFrame'); return; }
    if (hasInstallPrompt()) {
      const result = await showInstallPrompt();
      if (result === 'accepted') { setMessage(null); return; }
      if (result === 'dismissed') { setMessage('installDismissed'); return; }
    }
    setMessage(ios ? 'installIos' : mobile ? 'installAndroid' : 'installComputer');
  };
  return <section className="install-panel" aria-labelledby="install-title">
    <div className="install-top"><span className="install-icon"><Download size={21}/></span><div><h2 id="install-title">{t.installTitle}</h2><p>{t.installDescription}</p></div></div>
    <div className="install-actions">
      <button type="button" onClick={() => void install('mobile')}><Smartphone size={18}/>{t.installMobile}</button>
      <button type="button" onClick={() => void install('desktop')}><Monitor size={18}/>{t.installDesktop}</button>
    </div>
    <p className="install-caption">{t.installBrowser}</p>
    {message && <div className="install-message" role="status"><p>{t[message]}</p>{message === 'installInFrame' && <a href={location.href} target="_blank" rel="noopener noreferrer">{t.installOpenTab} ↗</a>}</div>}
  </section>;
}
