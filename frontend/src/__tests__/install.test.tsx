// @vitest-environment jsdom
import React from 'react';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {InstallPanel} from '../InstallPanel';
import {dictionary} from '../i18n';

const device = (userAgent: string, platform = 'Linux x86_64', maxTouchPoints = 0) => {
  Object.defineProperty(navigator, 'userAgent', {configurable:true, value:userAgent});
  Object.defineProperty(navigator, 'platform', {configurable:true, value:platform});
  Object.defineProperty(navigator, 'maxTouchPoints', {configurable:true, value:maxTouchPoints});
};
beforeEach(() => {
  Object.defineProperty(window, 'isSecureContext', {configurable:true, value:true});
  device('Desktop Chrome');
});
afterEach(() => {cleanup();vi.restoreAllMocks();});
describe('installation panel', () => {
  it('renders both buttons and directs a desktop user to their phone', () => {
    render(<InstallPanel t={dictionary.ar}/>);
    fireEvent.click(screen.getByRole('button', {name: /تحميل التطبيق على الجوال/}));
    expect(screen.getByRole('status').textContent).toBe(dictionary.ar.installMobileOther);
    expect(screen.getByRole('button', {name: /تحميل التطبيق على سطح المكتب/})).toBeTruthy();
  });
  it('explains Safari installation on iPhone without an automatic prompt', () => {
    device('iPhone Safari', 'iPhone', 5);
    render(<InstallPanel t={dictionary.en}/>);
    fireEvent.click(screen.getByRole('button', {name:'Install on mobile'}));
    expect(screen.getByRole('status').textContent).toBe(dictionary.en.installIos);
  });
  it('explains when a secure connection is missing', () => {
    Object.defineProperty(window, 'isSecureContext', {configurable:true, value:false});
    render(<InstallPanel t={dictionary.en}/>);
    fireEvent.click(screen.getByRole('button', {name:'Install on desktop'}));
    expect(screen.getByRole('status').textContent).toBe(dictionary.en.installInsecure);
  });
  it('uses a captured one-shot prompt and reports a dismissal', async () => {
    const prompt = vi.fn().mockResolvedValue(undefined);
    const event = new Event('beforeinstallprompt', {cancelable:true});
    Object.assign(event, {prompt, userChoice:Promise.resolve({outcome:'dismissed', platform:'web'})});
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    render(<InstallPanel t={dictionary.en}/>);
    fireEvent.click(screen.getByRole('button', {name:'Install on desktop'}));
    await waitFor(() => expect(screen.getByRole('status').textContent).toBe(dictionary.en.installDismissed));
    expect(prompt).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole('button', {name:'Install on desktop'}));
    expect(screen.getByRole('status').textContent).toBe(dictionary.en.installComputer);
    expect(prompt).toHaveBeenCalledOnce();
  });
  it('shows installed state when launched standalone', () => {
    vi.stubGlobal('matchMedia', () => ({matches:true}));
    render(<InstallPanel t={dictionary.en}/>);
    fireEvent.click(screen.getByRole('button', {name:'Install on desktop'}));
    expect(screen.getByRole('status').textContent).toBe(dictionary.en.installDone);
    vi.unstubAllGlobals();
  });
});
