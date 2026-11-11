// @vitest-environment jsdom
import React from 'react';
import {afterEach, describe, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {Alert, ImageMosaic, LedgerTable, StorageDialog, TextField} from '../components';
import {dictionary} from '../i18n';

afterEach(cleanup);
describe('prototype components', () => {
  it('exposes labelled field errors to assistive technology', () => {
    render(<TextField id="email" label="Email" error="Invalid email"/>);
    expect(screen.getByLabelText('Email').getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByLabelText('Email').getAttribute('aria-describedby')).toBe('email-error');
    expect(screen.getByText('Invalid email')).toBeTruthy();
  });
  it('uses the real minus sign and isolates signed ledger values', () => {
    render(<LedgerTable t={dictionary.en} entries={[{product_id:1,date:'2026-01-01',qty_start:20,qty_end:22,money_start:900,money_end:700}]}/>);
    expect(screen.getByText('−200$').getAttribute('dir')).toBe('ltr');
    expect(screen.getByText('+700$')).toBeTruthy();
  });
  it('renders the mosaic with zero through four pictures', () => {
    for (let n=0;n<=4;n++) {
      const {container,unmount}=render(<ImageMosaic alt="Farm" images={Array(n).fill('/farm.jpg')}/>);
      expect(container.querySelectorAll('img').length).toBe(n);
      expect(container.querySelector(`.mosaic-${n}`)).toBeTruthy();
      unmount();
    }
  });
  it('shows alerts with appropriate roles', () => {
    const {rerender}=render(<Alert>Wrong</Alert>);
    expect(screen.getByRole('alert').textContent).toContain('Wrong');
    rerender(<Alert kind="success">Saved</Alert>);
    expect(screen.getByRole('status').textContent).toContain('Saved');
  });
  it('traps focus and closes the storage dialog with Escape', () => {
    const close=vi.fn();
    render(<StorageDialog kind="subscription" storage={{status:'off'}} t={dictionary.en} onClose={close} onChange={()=>{}}/>);
    const modal=screen.getByRole('dialog');
    const buttons=modal.querySelectorAll('button');
    buttons[buttons.length-1].focus();
    fireEvent.keyDown(document,{key:'Tab'});
    expect(document.activeElement).toBe(buttons[0]);
    fireEvent.keyDown(document,{key:'Escape'});
    expect(close).toHaveBeenCalledOnce();
  });
});
